from conan import ConanFile

class ModuleConan(ConanFile):

    def requirements(self):
        self.requires("qt/1.0")
        self.requires("qcustomplot/1.0")
