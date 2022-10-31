from conan import ConanFile

class ModuleConan(ConanFile):

    def requirements(self):
        self.requires("qt/5.15.6")
        self.requires("qcustomplot/2.1.0")
