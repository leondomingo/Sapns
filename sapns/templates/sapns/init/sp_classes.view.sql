create view _view_sp_classes
as
select cls.id, cls.name as "{{_('Name')}}", cls.title as "{{_('Title')}}", 
  p_cls.name as "{{_('Parent class')}}"
from sp_classes cls
left join sp_classes p_cls on p_cls.id = cls.id_parent_class