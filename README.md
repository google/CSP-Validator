# CSP Validator

![image](http://aerotwist.com/cspvalidator/screenshot.png)

This is a [Sublime Text 2](http://www.sublimetext.com/) plugin that checks your
JavaScript, HTML and CSS for potential [Content Security Policy](https://developer.chrome.com/extensions/contentSecurityPolicy.html) issues. If you're new to Content Security Policy
there is, in fact, [an HTML5 Rocks article for that](http://www.html5rocks.com/en/tutorials/security/content-security-policy/)!

Right now the plugin checks for:

* Inline scripts
* Images and scripts with src attributes with http(s) protocols
* Use of eval or new Function
* setTimeout with a string param (this is only explicit usage of a string, not if it's passed as a variable)
* Attempting to load resources in CSS with http(s) protocols

## Installation

Right now you need to clone this repo into your packages folder
(typically ~/Library/Application Support/Sublime Text 2/Packages).

```
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages
git clone git://github.com/paullewis/CSP-Validator.git
```

_Please note: this is only an alpha release. Once all the issues are ironed out I'll request
to be added to Package Control._

## Usage

Just code away and all being well you will receive warnings as the plugin finds
them. If for any reason you want to disable the warnings you can use *Ctrl + Option + Shift + C* (or Alt on PC instead of Option) to disable the plugin.
