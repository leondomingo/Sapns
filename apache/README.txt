#Here is a numbered list of what you need to do to deploy your Turbogears2 or Pylons application. Follow 1 through 6. 

#1. Create production.ini configuration file if its not there already. Example: 
paster make-config exampletg production.ini
#Edit production.ini and comment out the port settings, update the url for the production database.

#2. Change or check the apache settings file.
#Edit /usr/local/turbogears/exampletg/apache/exampletg and make sure it has the necessary apache configurations you need. Please update any paths if youi are placing your app somewehere other then /usr/local/turbogears/exampletg/

#Copy {exampletg} apache config file to apache folder. Example:
cp /usr/local/turbogears/exampletg/apache/exampletg /etc/apache2/sites-available/exampletg

#3.Check if permissions are the same as other apache sites usually (root:root)

ls -l /etc/apache2/sites-available/
#You shoud see
#total 16
#-rw-r--r-- 1 root root  950 2008-08-08 13:06 default
#-rw-r--r-- 1 root root 7366 2008-08-08 13:06 default-ssl
#-rw-r--r-- 1 root root 1077 2008-11-08 12:38 exampletg

#4.Enable your site.
a2ensite exampletg

#5. Check if your project has proper permissions, usually apache user. (Example: www-data:www-data on Debian).
ls -l /usr/local/turbogears/exampletg/apache/
#total 16
#-rw-r--r-- 1 www-data www-data 1077 2008-11-26 22:35 exampletg
#-rw-r--r-- 1 www-data www-data 2319 2008-11-26 23:25 exampletg.wsgi
#-rw-r--r-- 1 www-data www-data  594 2008-11-26 22:35 README.txt
#-rw-r--r-- 1 www-data www-data  538 2008-11-26 22:35 test.wsgi

#6.Reload apache
/etc/init.d/apache2 reload


#You are done. Your application should be working. Check the access.log, warn.log, and error.log in /var/log/apache to see if there are any errors. 
