-- desc: init: sp_attributes
create or replace view _view_sp_attributes
as
select attr.id, attr.name as "Name", attr.title as "Title", 
  attr.type as "Type", 
  attr.required as "Required", attr.visible as "Visible", 
  attr.insertion_order as "Insertion order",
  attr.reference_order as "Reference order", 
  cls.name as "Class"
from sp_attributes attr
join sp_classes cls on cls.id = attr.id_class;