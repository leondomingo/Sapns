#!/bin/bash

echo "Controllers"
cp -R sapns/controllers/myapp sapns/controllers/$1

echo "CSS"
cp -R sapns/public/css/myapp sapns/public/css/$1

echo "JS"
cp -R sapns/public/js/myapp sapns/public/js/$1

echo "Images"
mkdir sapns/public/images/$1

echo "Templates"
cp -R sapns/templates/myapp/ sapns/templates/$1

echo "Ok!"

