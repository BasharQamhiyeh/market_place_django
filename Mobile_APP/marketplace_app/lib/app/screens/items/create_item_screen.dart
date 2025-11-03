import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/category_service.dart';
import '../../services/item_service.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;

class CreateItemScreen extends StatefulWidget {
  const CreateItemScreen({super.key});

  @override
  State<CreateItemScreen> createState() => _CreateItemScreenState();
}

class _CreateItemScreenState extends State<CreateItemScreen> {
  final _form = GlobalKey<FormState>();
  String title = '', description = '', condition = 'new', price = '';
  int? categoryId, cityId;
  bool loading = true;
  String? error;
  List<dynamic> categories = [];
  List<dynamic> cities = [];
  List<dynamic> images = [];
  List<dynamic> attributes = [];
  final Map<int, dynamic> attrValues = {};

  Future<void> _init() async {
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final catService = CategoryService(api);
      final _cats = await catService.getCategoriesTree();
      final _cities = await catService.getCities();
      setState(() {
        categories = _cats as List<dynamic>;
        cities = _cities as List<dynamic>;
        error = null;
      });
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
    }
  }

  void _onCategoryChanged(int? id) {
    setState(() {
      categoryId = id;
      attributes = [];
      attrValues.clear();
      if (id != null) {
        final cat = categories.firstWhere((c) => c['id'] == id);
        attributes = (cat['attributes'] as List?) ?? [];
      }
    });
  }

  @override
  void initState() {
    super.initState();
    _init();
  }

    

  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImages() async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.image,
      withData: kIsWeb, // ✅ read bytes for web
    );

    if (result != null) {
      setState(() {
        if (kIsWeb) {
          images = result.files
              .where((f) => f.bytes != null)
              .map((f) => f.bytes!)
              .toList(); // Uint8List
        } else {
          images = result.paths.whereType<String>().map((p) => File(p)).toList();
        }
      });
    }
  }



  List<Map<String, dynamic>> _buildAttributePayload() {
    return attrValues.entries
        .where((e) => e.value != null && e.value.toString().trim().isNotEmpty)
        .map((e) => {'attribute_id': e.key, 'value': e.value.toString()})
        .toList();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate() || categoryId == null || cityId == null) {
      return;
    }
    _form.currentState!.save();
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final svc = ItemService(api);

      final files = <http.MultipartFile>[];
      for (final img in images) {
        if (kIsWeb) {
          files.add(http.MultipartFile.fromBytes(
            'images',
            img as Uint8List,
            filename: 'upload_${DateTime.now().millisecondsSinceEpoch}.jpg',
          ));
        } else {
          files.add(await http.MultipartFile.fromPath('images', (img as File).path));
        }
      }

      await svc.createItem(
        title: title,
        condition: condition,
        price: price,
        description: description,
        cityId: cityId!,
        categoryId: categoryId!,
        images: files,
        attributeValues: _buildAttributePayload(),
      );

      if (mounted) Navigator.pop(context);
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Item')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Form(
                key: _form,
                child: Column(
                  children: [
                    TextFormField(
                      decoration: const InputDecoration(labelText: 'Title'),
                      onSaved: (v) => title = v!.trim(),
                      validator: (v) => v!.isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      decoration: const InputDecoration(labelText: 'Condition'),
                      items: const [
                        DropdownMenuItem(value: 'new', child: Text('New')),
                        DropdownMenuItem(value: 'used', child: Text('Used')),
                      ],
                      value: condition,
                      onChanged: (v) => setState(() => condition = v!),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      decoration: const InputDecoration(labelText: 'Price (JOD)'),
                      keyboardType: TextInputType.number,
                      onSaved: (v) => price = v!.trim(),
                      validator: (v) => v!.isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      maxLines: 4,
                      decoration: const InputDecoration(labelText: 'Description'),
                      onSaved: (v) => description = v!.trim(),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int>(
                      decoration: const InputDecoration(labelText: 'Category'),
                      value: categoryId,
                      items: categories
                          .map<DropdownMenuItem<int>>(
                            (c) => DropdownMenuItem(
                              value: c['id'] as int,
                              child: Text(c['name_en'] ?? c['name_ar'] ?? 'Category'),
                            ),
                          )
                          .toList(),
                      onChanged: _onCategoryChanged,
                      validator: (v) => v == null ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int>(
                      decoration: const InputDecoration(labelText: 'City'),
                      value: cityId,
                      items: cities
                          .map<DropdownMenuItem<int>>(
                            (c) => DropdownMenuItem(
                              value: c['id'] as int,
                              child: Text(c['name_en'] ?? c['name_ar'] ?? 'City'),
                            ),
                          )
                          .toList(),
                      onChanged: (v) => setState(() => cityId = v),
                      validator: (v) => v == null ? 'Required' : null,
                    ),
                    const SizedBox(height: 16),

                    // Dynamic attributes section
                    if (attributes.isNotEmpty) ...[
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          'Attributes',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(height: 8),
                      for (final a in attributes)
                        _AttrField(
                          attribute: a,
                          onChanged: (val) => attrValues[a['id'] as int] = val,
                        ),
                      const SizedBox(height: 16),
                    ],

                    Align(
                      alignment: Alignment.centerLeft,
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final img in images)
                            kIsWeb
                              ? Image.memory(img as Uint8List, width: 90, height: 90, fit: BoxFit.cover)
                              : Image.file(img as File, width: 90, height: 90, fit: BoxFit.cover),
                          OutlinedButton.icon(
                            onPressed: _pickImages,
                            icon: const Icon(Icons.add_a_photo),
                            label: const Text('Add photos'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (error != null)
                      Text(
                        error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _submit,
                        child: const Text('Create'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}

class _AttrField extends StatelessWidget {
  final Map<String, dynamic> attribute;
  final ValueChanged<dynamic> onChanged;

  const _AttrField({required this.attribute, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final inputType = attribute['input_type'] ?? 'text';
    final name = attribute['name_en'] ?? attribute['name_ar'] ?? 'Attribute';
    final required = attribute['is_required'] == true;
    final options = (attribute['options'] as List?) ?? [];

    switch (inputType) {
      case 'select':
        return DropdownButtonFormField<String>(
          decoration: InputDecoration(labelText: name),
          items: options
              .map<DropdownMenuItem<String>>(
                (o) => DropdownMenuItem(
                  value: (o['value_en'] ?? o['value_ar'] ?? '').toString(),
                  child: Text(o['value_en'] ?? o['value_ar'] ?? ''),
                ),
              )
              .toList(),
          onChanged: onChanged,
          validator: (v) =>
              required && (v == null || v.isEmpty) ? 'Required' : null,
        );
      default:
        return TextFormField(
          decoration: InputDecoration(labelText: name),
          onChanged: onChanged,
          validator: (v) =>
              required && (v == null || v.isEmpty) ? 'Required' : null,
        );
    }
  }
}
