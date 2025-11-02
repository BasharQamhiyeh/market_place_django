import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../providers/user_provider.dart';
import '../../services/item_service.dart';
import '../home/home_screen.dart';

class CreateItemScreen extends StatefulWidget {
  const CreateItemScreen({super.key});
  @override
  State<CreateItemScreen> createState() => _CreateItemScreenState();
}

class _CreateItemScreenState extends State<CreateItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final _picker = ImagePicker();

  // static fields
  String title = '';
  String condition = 'used';
  String price = '';
  String description = '';
  int? cityId;
  int? categoryId;

  // dynamic
  List<dynamic> cities = [];
  List<dynamic> categories = [];
  List<dynamic> attributes = []; // from /categories/:id/attributes/
  final Map<int, dynamic> attrValues = {};      // attr.id -> chosen value
  final Map<int, String> attrOtherValues = {};  // attr.id -> other text

  // images
  List<XFile> images = [];

  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _primeData();
  }

  Future<void> _primeData() async {
    try {
      final cts = await ItemService.fetchCities();
      final cats = await ItemService.fetchCategories();
      setState(() {
        cities = cts;
        categories = cats;
        loading = false;
      });
    } catch (e) {
      setState(() {
        error = "Failed to load initial data";
        loading = false;
      });
    }
  }

  Future<void> _onCategoryChanged(int? id) async {
    setState(() {
      categoryId = id;
      attributes = [];
      attrValues.clear();
      attrOtherValues.clear();
    });
    if (id == null) return;
    try {
      final attrs = await ItemService.fetchCategoryAttributes(id);
      setState(() => attributes = attrs);
    } catch (_) {
      setState(() => error = "Failed to load attributes");
    }
  }

  Future<void> _pickImages() async {
    final picked = await _picker.pickMultiImage(imageQuality: 85);
    if (picked.isNotEmpty) setState(() => images = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    // Build attributes payload
    final List<Map<String, dynamic>> payloadAttrs = [];
    for (final a in attributes) {
      final int id = a['id'];
      final String input = a['input_type'];
      final bool required = a['is_required'] == true;

      dynamic v = attrValues[id];
      if (input == 'select' && v == '__other__') {
        v = (attrOtherValues[id] ?? '').trim();
      }

      if (required && (v == null || (v is String && v.isEmpty))) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Field required: ${a['name_en'] ?? a['name_ar']}")),
        );
        return;
      }
      if (v != null && v.toString().isNotEmpty) {
        payloadAttrs.add({"id": id, "value": v.toString()});
      }
    }

    final token = context.read<UserProvider>().token;
    final ok = await ItemService.createItem(
      token: token!,
      title: title,
      condition: condition,
      price: price,
      description: description,
      categoryId: categoryId,
      cityId: cityId,
      attributes: payloadAttrs,
      images: images,
    );

    if (ok) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Failed to create item")),
      );
    }
  }

  Widget _buildAttributeField(Map a) {
    final int id = a['id'];
    final String label = (a['name_en'] ?? a['name_ar'] ?? '').toString();
    final String input = a['input_type'];
    final bool required = a['is_required'] == true;

    switch (input) {
      case 'number':
        return TextFormField(
          decoration: InputDecoration(labelText: label),
          keyboardType: TextInputType.number,
          onChanged: (v) => attrValues[id] = v,
          validator: (v) => required && (v == null || v.isEmpty) ? "Required" : null,
        );
      case 'select':
        final List opts = a['options'] ?? [];
        final items = <DropdownMenuItem<String>>[
          ...opts.map<DropdownMenuItem<String>>((o) => DropdownMenuItem(
                value: o['id'].toString(),
                child: Text(o['value_en'] ?? o['value_ar'] ?? ''),
              )),
          const DropdownMenuItem(value: '__other__', child: Text('Other')),
        ];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButtonFormField<String>(
              decoration: InputDecoration(labelText: label),
              value: attrValues[id] as String?,
              items: items,
              onChanged: (v) => setState(() => attrValues[id] = v),
              validator: (v) => required && (v == null || v.isEmpty) ? "Required" : null,
            ),
            if (attrValues[id] == '__other__')
              TextFormField(
                decoration: InputDecoration(labelText: "$label (Other)"),
                onChanged: (v) => attrOtherValues[id] = v,
                validator: (v) {
                  if (attrValues[id] == '__other__' && (v == null || v.isEmpty)) {
                    return "Required";
                  }
                  return null;
                },
              ),
          ],
        );
      default: // text
        return TextFormField(
          decoration: InputDecoration(labelText: label),
          onChanged: (v) => attrValues[id] = v,
          validator: (v) => required && (v == null || v.isEmpty) ? "Required" : null,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(title: const Text("Create Item")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Category
              DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: "Category"),
                value: categoryId,
                items: categories
                    .map<DropdownMenuItem<int>>((c) => DropdownMenuItem(
                          value: c['id'],
                          child: Text(c['name_en'] ?? c['name_ar'] ?? ''),
                        ))
                    .toList(),
                onChanged: _onCategoryChanged,
                validator: (v) => v == null ? "Required" : null,
              ),
              const SizedBox(height: 12),

              // Title
              TextFormField(
                decoration: const InputDecoration(labelText: "Title"),
                onChanged: (v) => title = v,
                validator: (v) => v == null || v.isEmpty ? "Required" : null,
              ),
              const SizedBox(height: 12),

              // Condition
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: "Condition"),
                value: condition,
                items: const [
                  DropdownMenuItem(value: "new", child: Text("New")),
                  DropdownMenuItem(value: "used", child: Text("Used")),
                ],
                onChanged: (v) => setState(() => condition = v ?? 'used'),
              ),
              const SizedBox(height: 12),

              // Price
              TextFormField(
                decoration: const InputDecoration(labelText: "Price (JOD)"),
                keyboardType: TextInputType.number,
                onChanged: (v) => price = v,
                validator: (v) => v == null || v.isEmpty ? "Required" : null,
              ),
              const SizedBox(height: 12),

              // City
              DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: "City"),
                value: cityId,
                items: cities
                    .map<DropdownMenuItem<int>>((c) => DropdownMenuItem(
                          value: c['id'],
                          child: Text(c['name_en'] ?? c['name_ar'] ?? ''),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => cityId = v),
              ),
              const SizedBox(height: 12),

              // Description
              TextFormField(
                decoration: const InputDecoration(labelText: "Description"),
                onChanged: (v) => description = v,
                maxLines: 4,
              ),
              const SizedBox(height: 16),

              // Dynamic attributes (after category selected)
              if (attributes.isNotEmpty)
                ...attributes.map<Widget>((a) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _buildAttributeField(Map<String, dynamic>.from(a)),
                    )),

              // Photos
              ElevatedButton.icon(
                onPressed: _pickImages,
                icon: const Icon(Icons.photo_library),
                label: const Text("Select Photos"),
              ),
              const SizedBox(height: 8),
              if (images.isNotEmpty)
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: images
                      .map((x) => Image.file(
                            File(x.path),
                            width: 100,
                            height: 100,
                            fit: BoxFit.cover,
                          ))
                      .toList(),
                ),
              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: _submit,
                child: const Text("Create Item"),
              ),
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(error!, style: const TextStyle(color: Colors.red)),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
