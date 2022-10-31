from conan import ConanFile


class QtConan(ConanFile):
    options = {
        "shared": [True, False],
        "with_atspi": [True, False],
    }

    default_options = {
        "shared": False,
        "with_atspi": False,
    }


    def config_options(self):
        self.options.with_atspi = False

    def configure(self):
        del self.options.with_atspi
