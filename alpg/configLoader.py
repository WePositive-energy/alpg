# Copyright (C) 2023 University of Twente

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from importlib.machinery import SourceFileLoader
import sys
import getopt

# Default write into a new folder
folder = "output/output/"

cfgOutputDir = "output/output/"
outputFolder = cfgOutputDir
cfgFile = None

# Parse arguments
opts, args = getopt.getopt(sys.argv[1:], "c:o:f", ["config=", "output=", "force"])
for opt, arg in opts:
    if opt in ("-c", "--config"):
        cfgFile = arg
    elif opt in ("-o", "--output"):
        cfgOutputDir = "output/" + arg + "/"

outputFolder = cfgOutputDir
sys.path.insert(0, "configs")


class ConfigLoader:
    def __new__(cls):
        """Make it a singleton"""
        if not hasattr(cls, "instance"):
            cls.instance = super(ConfigLoader, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.configModule = None

    def load_config(self, cfgFile):
        self.configModule = SourceFileLoader("config", cfgFile).load_module()

    def __getattr__(self, attr):
        return getattr(self.configModule, attr)

    def __hasattr__(self, attr):
        return hasattr(self.configModule, attr)


config = ConfigLoader()
