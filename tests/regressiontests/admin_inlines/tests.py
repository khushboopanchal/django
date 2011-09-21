from django.contrib.admin.helpers import InlineAdminForm
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

# local test models
from models import (Holder, Inner, Holder2, Inner2, Holder3,
    Inner3, Person, OutfitItem, Fashionista, Teacher, Parent, Child,
    CapoFamiglia, Consigliere, SottoCapo)
from admin import InnerInline


class TestInline(TestCase):
    urls = "regressiontests.admin_inlines.urls"
    fixtures = ['admin-views-users.xml']

    def setUp(self):
        holder = Holder(dummy=13)
        holder.save()
        Inner(dummy=42, holder=holder).save()
        self.change_url = '/admin/admin_inlines/holder/%i/' % holder.id

        result = self.client.login(username='super', password='secret')
        self.assertEqual(result, True)

    def tearDown(self):
        self.client.logout()

    def test_can_delete(self):
        """
        can_delete should be passed to inlineformset factory.
        """
        response = self.client.get(self.change_url)
        inner_formset = response.context[-1]['inline_admin_formsets'][0].formset
        expected = InnerInline.can_delete
        actual = inner_formset.can_delete
        self.assertEqual(expected, actual, 'can_delete must be equal')

    def test_readonly_stacked_inline_label(self):
        """Bug #13174."""
        holder = Holder.objects.create(dummy=42)
        inner = Inner.objects.create(holder=holder, dummy=42, readonly='')
        response = self.client.get('/admin/admin_inlines/holder/%i/'
                                   % holder.id)
        self.assertContains(response, '<label>Inner readonly label:</label>')

    def test_many_to_many_inlines(self):
        "Autogenerated many-to-many inlines are displayed correctly (#13407)"
        response = self.client.get('/admin/admin_inlines/author/add/')
        # The heading for the m2m inline block uses the right text
        self.assertContains(response, '<h2>Author-book relationships</h2>')
        # The "add another" label is correct
        self.assertContains(response, 'Add another Author-Book Relationship')
        # The '+' is dropped from the autogenerated form prefix (Author_books+)
        self.assertContains(response, 'id="id_Author_books-TOTAL_FORMS"')

    def test_inline_primary(self):
        person = Person.objects.create(firstname='Imelda')
        item = OutfitItem.objects.create(name='Shoes')
        # Imelda likes shoes, but can't cary her own bags.
        data = {
            'shoppingweakness_set-TOTAL_FORMS': 1,
            'shoppingweakness_set-INITIAL_FORMS': 0,
            'shoppingweakness_set-MAX_NUM_FORMS': 0,
            '_save': u'Save',
            'person': person.id,
            'max_weight': 0,
            'shoppingweakness_set-0-item': item.id,
        }
        response = self.client.post('/admin/admin_inlines/fashionista/add/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Fashionista.objects.filter(person__firstname='Imelda')), 1)

    def test_tabular_non_field_errors(self):
        """
        Ensure that non_field_errors are displayed correctly, including the
        right value for colspan. Refs #13510.
        """
        data = {
            'title_set-TOTAL_FORMS': 1,
            'title_set-INITIAL_FORMS': 0,
            'title_set-MAX_NUM_FORMS': 0,
            '_save': u'Save',
            'title_set-0-title1': 'a title',
            'title_set-0-title2': 'a different title',
        }
        response = self.client.post('/admin/admin_inlines/titlecollection/add/', data)
        # Here colspan is "4": two fields (title1 and title2), one hidden field and the delete checkbock.
        self.assertContains(response, '<tr><td colspan="4"><ul class="errorlist"><li>The two titles must be the same</li></ul></td></tr>')

    def test_no_parent_callable_lookup(self):
        """Admin inline `readonly_field` shouldn't invoke parent ModelAdmin callable"""
        # Identically named callable isn't present in the parent ModelAdmin,
        # rendering of the add view shouldn't explode
        response = self.client.get('/admin/admin_inlines/novel/add/')
        self.assertEqual(response.status_code, 200)
        # View should have the child inlines section
        self.assertContains(response, '<div class="inline-group" id="chapter_set-group">')

    def test_callable_lookup(self):
        """Admin inline should invoke local callable when its name is listed in readonly_fields"""
        response = self.client.get('/admin/admin_inlines/poll/add/')
        self.assertEqual(response.status_code, 200)
        # Add parent object view should have the child inlines section
        self.assertContains(response, '<div class="inline-group" id="question_set-group">')
        # The right callabe should be used for the inline readonly_fields
        # column cells
        self.assertContains(response, '<p>Callable in QuestionInline</p>')

    def test_help_text(self):
        """
        Ensure that the inlines' model field help texts are displayed when
        using both the stacked and tabular layouts.
        Ref #8190.
        """
        response = self.client.get('/admin/admin_inlines/holder4/add/')
        self.assertContains(response, '<p class="help">Awesome stacked help text is awesome.</p>', 4)
        self.assertContains(response, '<img src="/static/admin/img/icon-unknown.gif" class="help help-tooltip" width="10" height="10" alt="(Awesome tabular help text is awesome.)" title="Awesome tabular help text is awesome." />', 1)

    def test_non_related_name_inline(self):
        """
        Ensure that multiple inlines with related_name='+' have correct form
        prefixes. Bug #16838.
        """
        response = self.client.get('/admin/admin_inlines/capofamiglia/add/')

        self.assertContains(response,
                '<input type="hidden" name="-1-0-id" id="id_-1-0-id" />')
        self.assertContains(response,
                '<input type="hidden" name="-1-0-capo_famiglia" '
                'id="id_-1-0-capo_famiglia" />')
        self.assertContains(response,
                '<input id="id_-1-0-name" type="text" class="vTextField" '
                'name="-1-0-name" maxlength="100" />')

        self.assertContains(response,
                '<input type="hidden" name="-2-0-id" id="id_-2-0-id" />')
        self.assertContains(response,
                '<input type="hidden" name="-2-0-capo_famiglia" '
                'id="id_-2-0-capo_famiglia" />')
        self.assertContains(response,
                '<input id="id_-2-0-name" type="text" class="vTextField" '
                'name="-2-0-name" maxlength="100" />')


class TestInlineMedia(TestCase):
    urls = "regressiontests.admin_inlines.urls"
    fixtures = ['admin-views-users.xml']

    def setUp(self):

        result = self.client.login(username='super', password='secret')
        self.assertEqual(result, True)

    def tearDown(self):
        self.client.logout()

    def test_inline_media_only_base(self):
        holder = Holder(dummy=13)
        holder.save()
        Inner(dummy=42, holder=holder).save()
        change_url = '/admin/admin_inlines/holder/%i/' % holder.id
        response = self.client.get(change_url)
        self.assertContains(response, 'my_awesome_admin_scripts.js')

    def test_inline_media_only_inline(self):
        holder = Holder3(dummy=13)
        holder.save()
        Inner3(dummy=42, holder=holder).save()
        change_url = '/admin/admin_inlines/holder3/%i/' % holder.id
        response = self.client.get(change_url)
        self.assertContains(response, 'my_awesome_inline_scripts.js')

    def test_all_inline_media(self):
        holder = Holder2(dummy=13)
        holder.save()
        Inner2(dummy=42, holder=holder).save()
        change_url = '/admin/admin_inlines/holder2/%i/' % holder.id
        response = self.client.get(change_url)
        self.assertContains(response, 'my_awesome_admin_scripts.js')
        self.assertContains(response, 'my_awesome_inline_scripts.js')

class TestInlineAdminForm(TestCase):
    urls = "regressiontests.admin_inlines.urls"

    def test_immutable_content_type(self):
        """Regression for #9362
        The problem depends only on InlineAdminForm and its "original"
        argument, so we can safely set the other arguments to None/{}. We just
        need to check that the content_type argument of Child isn't altered by
        the internals of the inline form."""

        sally = Teacher.objects.create(name='Sally')
        john = Parent.objects.create(name='John')
        joe = Child.objects.create(name='Joe', teacher=sally, parent=john)

        iaf = InlineAdminForm(None, None, {}, {}, joe)
        parent_ct = ContentType.objects.get_for_model(Parent)
        self.assertEqual(iaf.original.content_type, parent_ct)
