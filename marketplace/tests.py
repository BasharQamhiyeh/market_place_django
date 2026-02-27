from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError

from marketplace.models import (
    User, Category, City, Listing, Item, Favorite,
    ItemPhoto, Attribute, AttributeOption, ItemAttributeValue,
)
from marketplace.models.users import normalize_jo_mobile_to_07

# Use simple static files storage in view tests to avoid manifest/missing-file issues.
SIMPLE_STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

class NormalizeJoMobileTests(TestCase):

    def test_local_format_unchanged(self):
        self.assertEqual(normalize_jo_mobile_to_07("0791234567"), "0791234567")

    def test_international_plus_prefix(self):
        self.assertEqual(normalize_jo_mobile_to_07("+962791234567"), "0791234567")

    def test_international_00_prefix(self):
        self.assertEqual(normalize_jo_mobile_to_07("00962791234567"), "0791234567")

    def test_international_no_plus(self):
        self.assertEqual(normalize_jo_mobile_to_07("962791234567"), "0791234567")

    def test_digits_starting_with_7(self):
        self.assertEqual(normalize_jo_mobile_to_07("791234567"), "0791234567")

    def test_strips_spaces(self):
        self.assertEqual(normalize_jo_mobile_to_07("079 123 4567"), "0791234567")

    def test_strips_dashes(self):
        self.assertEqual(normalize_jo_mobile_to_07("079-123-4567"), "0791234567")

    def test_empty_string_returns_empty(self):
        self.assertEqual(normalize_jo_mobile_to_07(""), "")

    def test_none_returns_empty(self):
        self.assertEqual(normalize_jo_mobile_to_07(None), "")


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class UserModelTests(TestCase):

    def test_create_user_sets_phone(self):
        user = User.objects.create_user(phone="0791111111", password="pass123")
        self.assertEqual(user.phone, "0791111111")

    def test_phone_normalised_on_save(self):
        user = User.objects.create_user(phone="+962791111111", password="pass123")
        self.assertEqual(user.phone, "0791111111")

    def test_referral_code_auto_generated(self):
        user = User.objects.create_user(phone="0792222222", password="pass123")
        self.assertIsNotNone(user.referral_code)
        self.assertEqual(len(user.referral_code), 12)

    def test_referral_code_unique(self):
        u1 = User.objects.create_user(phone="0793333333", password="pass123")
        u2 = User.objects.create_user(phone="0794444444", password="pass123")
        self.assertNotEqual(u1.referral_code, u2.referral_code)

    def test_duplicate_phone_raises(self):
        User.objects.create_user(phone="0795555555", password="pass123")
        with self.assertRaises(Exception):
            User.objects.create_user(phone="0795555555", password="pass456")

    def test_str_returns_phone(self):
        user = User.objects.create_user(phone="0796666666", password="pass123")
        self.assertEqual(str(user), "0796666666")

    def test_default_points_zero(self):
        user = User.objects.create_user(phone="0797777777", password="pass123")
        self.assertEqual(user.points, 0)

    def test_is_active_by_default(self):
        user = User.objects.create_user(phone="0798888888", password="pass123")
        self.assertTrue(user.is_active)


class CategoryModelTests(TestCase):

    def test_create_root_category(self):
        cat = Category.objects.create(name="Electronics")
        self.assertEqual(cat.name, "Electronics")
        self.assertIsNone(cat.parent)

    def test_create_subcategory(self):
        parent = Category.objects.create(name="Electronics")
        child = Category.objects.create(name="Phones", parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.subcategories.all())

    def test_str_returns_name(self):
        cat = Category.objects.create(name="Furniture")
        self.assertEqual(str(cat), "Furniture")

    def test_photo_url_returns_none_without_photo(self):
        cat = Category.objects.create(name="Books")
        self.assertIsNone(cat.photo_url)


class ListingModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000001", password="pass123")
        self.category = Category.objects.create(name="Test Category")
        self.city = City.objects.create(name="Amman")

    def _make_listing(self, **kwargs):
        defaults = dict(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Test Listing",
            is_approved=True,
            is_active=True,
        )
        defaults.update(kwargs)
        return Listing.objects.create(**defaults)

    def test_create_listing(self):
        listing = self._make_listing()
        self.assertEqual(listing.title, "Test Listing")
        self.assertEqual(listing.type, "item")

    def test_is_featured_false_when_no_featured_until(self):
        listing = self._make_listing()
        self.assertFalse(listing.is_featured)

    def test_is_featured_true_when_future_date(self):
        future = timezone.now() + timezone.timedelta(days=7)
        listing = self._make_listing(featured_until=future)
        self.assertTrue(listing.is_featured)

    def test_is_featured_false_when_past_date(self):
        past = timezone.now() - timezone.timedelta(days=1)
        listing = self._make_listing(featured_until=past)
        self.assertFalse(listing.is_featured)

    def test_default_not_approved(self):
        # New listings should default to unapproved
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Unapproved",
        )
        self.assertFalse(listing.is_approved)

    def test_str_includes_title_and_type(self):
        listing = self._make_listing(title="My Phone", type="item")
        self.assertIn("My Phone", str(listing))
        self.assertIn("item", str(listing))


class ItemModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000002", password="pass123")
        self.category = Category.objects.create(name="Items Cat")
        self.city = City.objects.create(name="Zarqa")
        self.listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Laptop",
            is_approved=True,
            is_active=True,
        )

    def test_create_item(self):
        item = Item.objects.create(listing=self.listing, price=500, condition="used")
        self.assertEqual(item.price, 500)
        self.assertEqual(item.condition, "used")

    def test_str_returns_title(self):
        item = Item.objects.create(listing=self.listing, price=500, condition="new")
        self.assertEqual(str(item), "Laptop")

    def test_main_photo_returns_none_when_no_photos(self):
        item = Item.objects.create(listing=self.listing, price=500, condition="new")
        self.assertIsNone(item.main_photo)

    def test_one_to_one_listing_constraint(self):
        Item.objects.create(listing=self.listing, price=100, condition="new")
        with self.assertRaises(Exception):
            Item.objects.create(listing=self.listing, price=200, condition="used")


class FavoriteModelTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(phone="0791000003", password="pass123")
        self.user2 = User.objects.create_user(phone="0791000004", password="pass123")
        self.category = Category.objects.create(name="Fav Cat")
        self.city = City.objects.create(name="Irbid")
        self.listing = Listing.objects.create(
            type="item",
            user=self.user1,
            category=self.category,
            city=self.city,
            title="Fav Item",
            is_approved=True,
            is_active=True,
        )

    def test_create_favorite(self):
        fav = Favorite.objects.create(user=self.user2, listing=self.listing)
        self.assertEqual(fav.user, self.user2)
        self.assertEqual(fav.listing, self.listing)

    def test_duplicate_favorite_raises(self):
        Favorite.objects.create(user=self.user2, listing=self.listing)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.user2, listing=self.listing)

    def test_different_users_can_favorite_same_listing(self):
        Favorite.objects.create(user=self.user1, listing=self.listing)
        Favorite.objects.create(user=self.user2, listing=self.listing)
        self.assertEqual(Favorite.objects.filter(listing=self.listing).count(), 2)


class CityModelTests(TestCase):

    def test_create_city(self):
        city = City.objects.create(name="Aqaba")
        self.assertEqual(city.name, "Aqaba")
        self.assertTrue(city.is_active)

    def test_unique_name_constraint(self):
        City.objects.create(name="Madaba")
        with self.assertRaises(Exception):
            City.objects.create(name="Madaba")

    def test_str_returns_name(self):
        city = City.objects.create(name="Karak")
        self.assertEqual(str(city), "Karak")


class AttributeModelTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Attr Cat")

    def test_create_attribute(self):
        attr = Attribute.objects.create(
            name="Color",
            input_type="text",
            category=self.category,
        )
        self.assertEqual(attr.name, "Color")
        self.assertTrue(attr.is_required)

    def test_attribute_option(self):
        attr = Attribute.objects.create(
            name="Size",
            input_type="select",
            category=self.category,
        )
        opt = AttributeOption.objects.create(value="Large", attribute=attr)
        self.assertEqual(opt.attribute, attr)
        self.assertIn(opt, attr.options.all())


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

@override_settings(STORAGES=SIMPLE_STORAGES)
class HomeViewTests(TestCase):

    def test_home_returns_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")


@override_settings(STORAGES=SIMPLE_STORAGES)
class ItemListViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000010", password="pass123")
        self.category = Category.objects.create(name="List Cat")
        self.city = City.objects.create(name="List City")

    def _make_approved_item(self, title="Test Item", price=100):
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title=title,
            is_approved=True,
            is_active=True,
        )
        return Item.objects.create(listing=listing, price=price, condition="used")

    def test_item_list_returns_200(self):
        response = self.client.get(reverse("item_list"))
        self.assertEqual(response.status_code, 200)

    def test_item_list_shows_approved_items(self):
        self._make_approved_item(title="Visible Item")
        response = self.client.get(reverse("item_list"))
        self.assertContains(response, "Visible Item")

    def test_item_list_hides_unapproved_items(self):
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Hidden Item",
            is_approved=False,
            is_active=True,
        )
        Item.objects.create(listing=listing, price=50, condition="new")
        response = self.client.get(reverse("item_list"))
        self.assertNotContains(response, "Hidden Item")

    def test_item_list_search_filter(self):
        self._make_approved_item(title="Blue Bicycle")
        self._make_approved_item(title="Red Chair")
        response = self.client.get(reverse("item_list"), {"q": "Bicycle"})
        self.assertEqual(response.status_code, 200)


@override_settings(STORAGES=SIMPLE_STORAGES)
class ItemDetailViewTests(TestCase):

    def setUp(self):
        # first_name must be set — item_detail.html uses {{ user.first_name|first|upper }}
        self.user = User.objects.create_user(
            phone="0791000011", password="pass123", first_name="Test"
        )
        self.category = Category.objects.create(name="Detail Cat")
        self.city = City.objects.create(name="Detail City")

    def _make_approved_item(self, title="Detail Item"):
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title=title,
            is_approved=True,
            is_active=True,
        )
        return Item.objects.create(listing=listing, price=200, condition="new")

    def test_approved_item_returns_200(self):
        item = self._make_approved_item()
        response = self.client.get(reverse("item_detail", args=[item.id]))
        self.assertEqual(response.status_code, 200)

    def test_unapproved_item_returns_404(self):
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Unapproved",
            is_approved=False,
            is_active=True,
        )
        item = Item.objects.create(listing=listing, price=100, condition="new")
        response = self.client.get(reverse("item_detail", args=[item.id]))
        self.assertEqual(response.status_code, 404)

    def test_deleted_item_returns_404(self):
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="Deleted",
            is_approved=True,
            is_active=True,
            is_deleted=True,
        )
        item = Item.objects.create(listing=listing, price=100, condition="new")
        response = self.client.get(reverse("item_detail", args=[item.id]))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_item_returns_404(self):
        response = self.client.get(reverse("item_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_item_detail_increments_views(self):
        item = self._make_approved_item()
        initial_views = item.listing.views_count
        self.client.get(reverse("item_detail", args=[item.id]))
        item.listing.refresh_from_db()
        self.assertEqual(item.listing.views_count, initial_views + 1)

    def test_item_detail_does_not_double_count_in_same_session(self):
        item = self._make_approved_item()
        self.client.get(reverse("item_detail", args=[item.id]))
        self.client.get(reverse("item_detail", args=[item.id]))
        item.listing.refresh_from_db()
        self.assertEqual(item.listing.views_count, 1)


@override_settings(STORAGES=SIMPLE_STORAGES)
class ItemCreateViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000012", password="pass123")

    def test_create_item_redirects_to_login_for_anonymous(self):
        response = self.client.get(reverse("create_item"))
        self.assertRedirects(
            response,
            f"/login/?next={reverse('create_item')}",
            fetch_redirect_response=False,
        )

    def test_create_item_renders_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("create_item"))
        self.assertEqual(response.status_code, 200)


@override_settings(STORAGES=SIMPLE_STORAGES)
class AuthViewTests(TestCase):
    """
    The login view (user_login) is POST-only.
    A GET request to /login/ redirects to / (home).
    On failed login, it redirects back to the referer with ?login_error=1.
    On successful login, it redirects to home (or 'next').
    """

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000020", password="testpass123")

    def test_login_get_redirects_to_home(self):
        # The login view only handles POST; GET is redirected to /
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_login_with_correct_credentials_redirects(self):
        response = self.client.post(reverse("login"), {
            "username": "0791000020",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_redirects_with_error(self):
        # Wrong credentials → redirect back to referer with ?login_error=1
        response = self.client.post(reverse("login"), {
            "username": "0791000020",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("login_error=1", response["Location"])

    def test_login_with_unknown_phone_redirects_with_error(self):
        response = self.client.post(reverse("login"), {
            "username": "0799000000",
            "password": "any",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("login_error=1", response["Location"])

    def test_logout_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertIn(response.status_code, [301, 302])

    def test_register_page_renders(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)


@override_settings(STORAGES=SIMPLE_STORAGES)
class FavoriteToggleViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000030", password="pass123")
        self.owner = User.objects.create_user(phone="0791000031", password="pass123")
        self.category = Category.objects.create(name="Fav Toggle Cat")
        self.city = City.objects.create(name="Fav Toggle City")
        self.listing = Listing.objects.create(
            type="item",
            user=self.owner,
            category=self.category,
            city=self.city,
            title="Fav Toggle Item",
            is_approved=True,
            is_active=True,
        )
        self.item = Item.objects.create(listing=self.listing, price=50, condition="new")

    def test_toggle_favorite_requires_login(self):
        response = self.client.post(
            reverse("toggle_favorite", args=[self.item.id])
        )
        self.assertIn(response.status_code, [301, 302])
        # Should not create a favorite
        self.assertFalse(Favorite.objects.filter(listing=self.listing).exists())

    def test_toggle_favorite_adds_favorite(self):
        self.client.force_login(self.user)
        self.client.post(reverse("toggle_favorite", args=[self.item.id]))
        self.assertTrue(
            Favorite.objects.filter(user=self.user, listing=self.listing).exists()
        )

    def test_toggle_favorite_removes_existing_favorite(self):
        self.client.force_login(self.user)
        Favorite.objects.create(user=self.user, listing=self.listing)
        self.client.post(reverse("toggle_favorite", args=[self.item.id]))
        self.assertFalse(
            Favorite.objects.filter(user=self.user, listing=self.listing).exists()
        )


@override_settings(STORAGES=SIMPLE_STORAGES)
class MyItemsViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone="0791000040", password="pass123")
        self.category = Category.objects.create(name="My Items Cat")
        self.city = City.objects.create(name="My Items City")

    def test_my_items_redirects_for_anonymous(self):
        response = self.client.get(reverse("my_items"))
        self.assertIn(response.status_code, [301, 302])

    def test_my_items_renders_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("my_items"))
        self.assertEqual(response.status_code, 200)

    def test_my_items_shows_own_items(self):
        self.client.force_login(self.user)
        listing = Listing.objects.create(
            type="item",
            user=self.user,
            category=self.category,
            city=self.city,
            title="My Own Item",
            is_approved=True,
            is_active=True,
        )
        Item.objects.create(listing=listing, price=99, condition="used")
        response = self.client.get(reverse("my_items"))
        self.assertContains(response, "My Own Item")

    def test_my_items_does_not_show_others_items(self):
        other_user = User.objects.create_user(phone="0791000041", password="pass123")
        listing = Listing.objects.create(
            type="item",
            user=other_user,
            category=self.category,
            city=self.city,
            title="Other User Item",
            is_approved=True,
            is_active=True,
        )
        Item.objects.create(listing=listing, price=99, condition="used")
        self.client.force_login(self.user)
        response = self.client.get(reverse("my_items"))
        self.assertNotContains(response, "Other User Item")


@override_settings(STORAGES=SIMPLE_STORAGES)
class StaticPagesTests(TestCase):

    def test_about_page_renders(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_faq_page_renders(self):
        response = self.client.get(reverse("faq"))
        self.assertEqual(response.status_code, 200)

    def test_privacy_page_renders(self):
        response = self.client.get(reverse("privacy_policy"))
        self.assertEqual(response.status_code, 200)

    def test_contact_support_renders(self):
        response = self.client.get(reverse("contact_support"))
        self.assertEqual(response.status_code, 200)
