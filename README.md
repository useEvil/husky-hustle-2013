husky-hustle
============

Fundraising website for Managing Registrants, Sponsors and Donations.  Built using Python's Django Framework.  I did this as a volunteer 
for Daughters Elementary School over a one month period.  It has a lot of basic features and third-party integration.  The site allows 
Parents to manage Sponsors and Donations.  Parents can view the list of Donations by Student and send Email Reminders for Sponsors to make 
payments.  A Printable Donation Sheet is available for record keeping or submitting to the School.  Visitors can also make donations if 
they know the Student's Identifier or Donation Link, which can be posted to Facebook or Twitter.  A Photo Gallery is available which integrates 
with Picasa.  There is a simple Blog (with RSS Feed) to post updates.  A simple Contact Us form.  Goole Calendar has been integrated to 
pull event dates.  There is a simple Message of the Week option.  There is also a rising Thermometer so visitors can keep track of the 
progress of the Fundraiser.  Results are calculated and graphed so users and admins can visually see how the Fundraiser is doing.

The Django admin interface allows administers to manage all the data collected through the site.

Features
--------

1. Parent Registration
    * account linking
2. Students (related to Parents)
    * Adding
    * Modifying
    * Searching
3. Donators/Sponsors for a Student
    * Adding
    * Modifying
    * Deleting
    * Printing
4. Collecting Donations
    * TODO: Payment Processor Integration
5. Emails
    * Reminders
    * Invitations
6. Social integration
    * Facebook
    * Twitter
    * Google+
7. Photo Gallery integration
    * Picasa
8. Calendar
    * Google Calendar
9. Contact Form
10. Fundraising Thermometer
    * Main Goal
    * Total Pledged
    * Total Collected
11. Content
    * Blogging
        * RSS Feed
    * Message of the Week
    * Important Links
    * Mobile Version
12. Reporting
    * Graphing of Most Laps By Grade
    * Graphing of Most Donations By Grade
    * Graphing of Most Laps By Child By Grade
    * Graphing of Most Donations By Child By Grade

Dependencies
------------

* [Python](http://www.python.org/) - http://www.python.org/
* [Gdata](https://code.google.com/p/gdata-python-client/) - https://code.google.com/p/gdata-python-client/
* [Django](http://www.djangoproject.com/) - https://www.djangoproject.com/
* [django-registration](http://www.djangoproject.com/) - http://code.google.com/p/django-registration/
* [django-socialregistration](https://github.com/flashingpumpkin/django-socialregistration/) - https://github.com/flashingpumpkin/django-socialregistration/
* [django-picasa](http://code.google.com/p/django-picasa/) - http://code.google.com/p/django-picasa/
* [djangorestframework==0.4.0](http://django-rest-framework.org/) - http://django-rest-framework.org/
* [newrelic](https://rpm.newrelic.com/) - https://rpm.newrelic.com/ (for production)

Frameworks
----------

* [jQuery](http://http://jquery.com/) - http://http://jquery.com/
* [jQuery UI](http://jqueryui.com/) - http://jqueryui.com/
* [Flexigrid](http://flexigrid.info/) - http://flexigrid.info/
* [Axiom CSS Template](http://www.freecsstemplates.org/preview/axiom/) - http://www.freecsstemplates.org/preview/axiom/
* [Hoverbox](http://host.sonspring.com/hoverbox/) - http://host.sonspring.com/hoverbox.
* [CSS Decorative Gallery](http://webdesignerwall.com/tutorials/css-decorative-gallery/) - http://webdesignerwall.com/tutorials/css-decorative-gallery/
* [InfoVis Toolkit ](http://philogb.github.com/jit/) - http://philogb.github.com/jit/

To Do
-----

1. Dependencies
    * update djangorestframework to 2.x
2. Content
   * Docs (Google Docs)
3. Payment Processor
   * Intuit

License
-------

husky-hustle is provided under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0). Commercial use requires attribution.

Credits
-------

husky-hustle is a project by [Thai Nguyen](http://www.thaiandhien.com/).