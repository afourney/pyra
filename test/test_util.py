# Load what we actually need to run the tests
import unittest
import pyra.util as util

class TestUtils(unittest.TestCase):

    def setUp(self):
        pass

    def test_binary_search(self):
        s = range(1,100,2)

        # Extermities
        self.assertEqual( util.binary_search(s, -1), 0 )
        self.assertEqual( util.binary_search(s, 0),  0 )
        self.assertEqual( util.binary_search(s, 1),  0 )
        self.assertEqual( util.binary_search(s, 2),  1 )

        l = len(s)
        self.assertEqual( util.binary_search(s, 101),  l )
        self.assertEqual( util.binary_search(s, 100),  l )
        self.assertEqual( util.binary_search(s, 99),  l-1 )
        self.assertEqual( util.binary_search(s, 98),  l-1 )

        # Inside
        for i in range(0,len(s)):
            # Things that are found
            self.assertEqual( util.binary_search(s, s[i]), i )

            # Things that are not found
            self.assertEqual( util.binary_search(s, s[i]-1), i )
            


    def test_galloping_search(self):
        s = range(1,100,2)

        # Extermities
        self.assertEqual( util.galloping_search(s, -1), 0 )
        self.assertEqual( util.galloping_search(s, 0),  0 )
        self.assertEqual( util.galloping_search(s, 1),  0 )
        self.assertEqual( util.galloping_search(s, 2),  1 )

        l = len(s)
        self.assertEqual( util.galloping_search(s, 101),  l )
        self.assertEqual( util.galloping_search(s, 100),  l )
        self.assertEqual( util.galloping_search(s, 99),  l-1 )
        self.assertEqual( util.galloping_search(s, 98),  l-1 )

        # Inside
        for i in range(0,len(s)):
            # Things that are found
            self.assertEqual( util.galloping_search(s, s[i]), i )

            # Things that are not found
            self.assertEqual( util.galloping_search(s, s[i]-1), i )

        # Hints
        for i in range(0,len(s)):
            for j in range(0,len(s)):
                # Things that are found
                self.assertEqual( util.galloping_search(s, s[i]), i, j )

                # Things that are not found
                self.assertEqual( util.galloping_search(s, s[i]-1), i, j )
