import excepthook_override
import os
import sys
ex = excepthook_override.Except()
ex.run_excepthook("hello")

import nose
n = 1/0
print "hello world 2!"