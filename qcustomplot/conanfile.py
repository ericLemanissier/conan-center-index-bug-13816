from conan import ConanFile

class QcustomplotConan(ConanFile):
    def configure(self):
        self.options["qt"].shared = True

    def requirements(self):
        self.requires("qt/1.0")
