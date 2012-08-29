-- __code__ = "sp_class_by_name" and "sp_attribute_by_name"

create or replace function sp_class_by_name(class_name varchar) returns integer
as
$$
begin
  return (select id from sp_classes
          where upper(name) = upper(class_name));
end;
$$
language plpgsql;

--#

create or replace function sp_attribute_by_name(class_name varchar, attr_name varchar) 
returns integer
as
$$
begin
  return (select a.id from sp_attributes a
          join sp_classes c on c.id = a.id_class
          where upper(c.name) = upper(class_name) and
                upper(a.name) = upper(attr_name));
end;
$$
language plpgsql;