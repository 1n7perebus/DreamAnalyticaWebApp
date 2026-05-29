from django.db import migrations, models
from django.db.models.functions import Lower


def _normalize_symbol_name(value):
    if not value:
        return ''
    return ' '.join(str(value).strip().split()).title()


def merge_case_variant_symbols(apps, schema_editor):
    DreamSymbol = apps.get_model('main', 'DreamSymbol')
    through = DreamSymbol.dreams.through

    dream_fk = None
    symbol_fk = None
    for field in through._meta.fields:
        if getattr(field, 'related_model', None) is None:
            continue
        model_name = field.related_model._meta.model_name
        if model_name == 'dreams':
            dream_fk = field.attname
        elif model_name == 'dreamsymbol':
            symbol_fk = field.attname

    if not dream_fk or not symbol_fk:
        return

    groups = {}
    for symbol in DreamSymbol.objects.all().order_by('id'):
        normalized = _normalize_symbol_name(symbol.name)
        if not normalized:
            continue
        key = normalized.casefold()
        groups.setdefault(key, {'normalized': normalized, 'symbols': []})
        groups[key]['symbols'].append(symbol)

    for payload in groups.values():
        normalized = payload['normalized']
        symbols = payload['symbols']
        if not symbols:
            continue

        keep = symbols[0]
        if keep.name != normalized:
            keep.name = normalized
            keep.save(update_fields=['name'])

        for duplicate in symbols[1:]:
            rel_qs = through.objects.filter(**{symbol_fk: duplicate.id}).values_list(dream_fk, flat=True)
            for dream_id in rel_qs:
                through.objects.get_or_create(**{dream_fk: dream_id, symbol_fk: keep.id})
            through.objects.filter(**{symbol_fk: duplicate.id}).delete()
            duplicate.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_dream_symbols'),
    ]

    operations = [
        migrations.RunPython(merge_case_variant_symbols, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='dreamsymbol',
            constraint=models.UniqueConstraint(
                Lower('name'),
                name='main_dreamsymbol_name_ci_unique',
            ),
        ),
    ]
