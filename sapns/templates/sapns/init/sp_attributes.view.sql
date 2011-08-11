create or replace view _view_sp_attributes
as
select attr.id, attr.name as "{{_('Name')}}", attr.title as "{{_('Title')}}", 
  attr.type as "{{_('Type')}}", 
  attr.required as "{{_('Required')}}", attr.visible as "{{_('Visible')}}", 
  attr.insertion_order as "{{_('Insertion order')}}",
  attr.reference_order as "{{_('Reference order')}}", 
  cls.name as "{{_('Class')}}"
from sp_attributes attr
join sp_classes cls on cls.id = attr.id_class