import sublime
import sublime_plugin
import re


class CSPRule():
    """ Represents a validation rule """
    rule = None
    message = None
    setting = None

    def __init__(self, rule, message, setting=None):
        self.rule = rule
        self.message = message
        self.setting = setting


class CSPError:
    """ Represents an error """
    region = None
    message = ''

    def __init__(self, region, message):
        self.region = region
        self.message = message


class CSPValidator():
    """ Runs the validation rules """

    rules = [

        # Matches on src attributes with an http[s] protocol
        CSPRule(
            "<(img|script).*?\ssrc\s?=\s?[\"']+http[^\"\']*[\"\']?",
            "External resources are not allowed",
            "csp_chromeapps"
        ),

        # Matches on src attributes with an http[s] protocol
        CSPRule(
            "<link.+?href\s?=\s?[\"']+http[^\"\']*[\"\']?",
            "External resources are not allowed",
            "csp_chromeapps"
        ),

        # Matches on scripts with non-whitespace contents
        CSPRule(

            # Opening tag
            "(?ms)<script[^>]*>[^<]+?" +

            # Non-whitespace chars that are _not_ closing the tag
            "[^\s<]+?" +

            # Now non-greedy fill to the end of the tag
            ".*?</script>",

            "Inline scripts are not allowed"
        ),

        # Matches on eval / new Function
        CSPRule(
            "eval|new Function",
            "Code creation from strings, e.g. eval / new Function not allowed"
        ),

        # Matches on eval / new Function
        CSPRule(
            "setTimeout\s?\(\"[^\"]*\"",
            "Code creation from strings, e.g. setTimeout(\"string\") is not allowed"
        ),

        # Matches on on{event}
        CSPRule(
            "<.*?\son[^>]*?>",
            "Event handlers should be added from an external src file"
        ),

        # Matches external resources in CSS
        CSPRule(
            "url\(\"?(?:https?:)?//[^\)]*\)",
            "External resources are not allowed",
            "csp_chromeapps"
        ),

        # Matches hrefs with a javascript: url
        CSPRule(
            "<.*?href.*?javascript:.*?>",
            "Inline JavaScript calls are not allowed",
            "csp_chromeapps"
        )
    ]

    def get_view_contents(self, view):
        return view.substr(sublime.Region(0, view.size()))

    def validate_contents(self, view):
        errors = []

        for rule in self.rules:
            # Check for any specific settings that govern the
            # assertion of this particular rule
            if(rule.setting == None or view.settings().get(rule.setting) == 1):
                matches = view.find_all(rule.rule, sublime.IGNORECASE)
                for match in matches:
                    errors.append(
                        CSPError(match, rule.message)
                    )

        return errors


class CSPValidatorCommand(sublime_plugin.EventListener):
    """ Main Validator Class """
    errors = None
    pluginSettings = None
    validator = CSPValidator()

    # these are the default settings. They are overridden and
    # documented in the GLShaderValidator.sublime-settings file
    DEFAULT_SETTINGS = {
        "csp_enabled": 1,
        "csp_chromeapps": 0
    }

    def __init__(self):
        """ Startup """

    def clear_settings(self):
        """ Resets the settings value """
        for window in sublime.windows():
            for view in window.views():
                if view.settings().get('csp_configured') != None:
                    view.settings().set('csp_configured', None)

    def apply_settings(self, view):
        """ Loads in and applies the settings file """

        # Lazy load in the settings file
        if self.pluginSettings == None:
            self.pluginSettings = sublime.load_settings(__name__ + ".sublime-settings")
            self.pluginSettings.clear_on_change('csp_validator')
            self.pluginSettings.add_on_change('csp_validator', self.clear_settings)

        # Only configure this view if it's not been done before
        if view.settings().get('csp_configured') == None:

            view.settings().set('csp_configured', True)

            # Go through the default settings
            for setting in self.DEFAULT_SETTINGS:

                # set the value
                settingValue = self.DEFAULT_SETTINGS[setting]

                # check if the user has overwritten the value
                # and switch to that instead
                if self.pluginSettings.get(setting) != None:
                    settingValue = self.pluginSettings.get(setting)

                view.settings().set(setting, settingValue)

    def clear_errors(self, view):
        """ Removes any errors """
        view.erase_regions('cspvalidator_errors')

    def is_valid_file_type(self, view):
        """ Checks that the file is worth checking """
        syntax = view.settings().get('syntax')
        isValidFile = False
        if syntax != None:
            isValidFile = re.search('html|javascript|css', syntax, flags=re.IGNORECASE) != None
        return isValidFile

    def show_errors(self, view):
        """ Passes over the array of errors and adds outlines """

        # Go through the errors that came back
        errorRegions = []
        for error in self.errors:
            errorRegions.append(error.region)

        # Put an outline around each one and a dot on the line
        view.add_regions(
            'cspvalidator_errors',
            errorRegions,
            'cspvalidation_error',
            'dot',
            sublime.DRAW_OUTLINED
        )

    def on_selection_modified(self, view):
        """ Shows a status message for an error region """

        view.erase_status('cspvalidation_error')

        # If we have errors just locate
        # the first one and go with that for the status
        if self.errors != None:
            for sel in view.sel():
                for error in self.errors:
                    if error.region.contains(sel):
                        view.set_status('cspvalidation_error',
                            error.message)
                        return

    def on_load(self, view):
        """ File loaded """
        self.run_validator(view)

    def on_activated(self, view):
        """ File activated """
        self.run_validator(view)

    def on_post_save(self, view):
        """ File saved """
        self.run_validator(view)

    def run_validator_all_views(self):
        for window in sublime.windows():
            for view in window.views():
                self.run_validator(view)

    def run_validator(self, view):
        """ Runs a validation pass """

        # clear the last run
        view.erase_status('cspvalidation_error')

        # set up the settings if necessary
        self.apply_settings(view)

        # early return if they have disabled the linter
        if view.settings().get('csp_enabled') == 0:
            self.clear_errors(view)
            return

        # early return for anything not using the correct syntax
        if not self.is_valid_file_type(view):
            return

        # Clear the last set of errors
        self.clear_errors

        # Get the file and send to the validator
        self.errors = self.validator.validate_contents(view)
        if self.errors != None:
            self.show_errors(view)


class ContentSecurityPolicyToggleCommand(sublime_plugin.ApplicationCommand):
    """ Toggles the CSP validation on and off """
    def run(self):
        # Get the settings for the plugin
        currentSettings = sublime.load_settings(__name__ + '.sublime-settings')
        setting = "csp_enabled"

        # Invert the values
        currentSettings.set(setting, 1 - currentSettings.get(setting))

        # Now save
        sublime.save_settings(__name__ + '.sublime-settings')

        # And force a clear out and re-run
        validator = CSPValidatorCommand()
        validator.clear_settings()
        validator.run_validator_all_views()
