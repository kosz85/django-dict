from unittest import TestCase, main
from src.todict import FormatedDict


class TestFormatedDict(TestCase):
    def setUp(self):
        self.data = {
            'a': 'A',
            'abc': ['a', 'b', 'c'],
            'b': {
                'c': 'C',
                'def': {'d': 'D',
                        'e': 'E',
                        'f': 'F'}
            },
            'z': [
                {'x': 'X1'},
                {'x': 'X2'},
                {'x': 'X3'}
            ]
        }

    def test_rm(self):
        self.assertIn('a', self.data)
        FormatedDict._rm(self.data, ['a'])
        self.assertNotIn('a', self.data)

        self.assertIn('abc', self.data)
        self.assertIn('b', self.data['abc'])
        FormatedDict._rm(self.data, ['abc', '!1'])
        self.assertNotIn('b', self.data['abc'])

        FormatedDict._rm(self.data, ['abc', '!999'])

        self.assertIn('abc', self.data)
        FormatedDict._rm(self.data, ['abc'])
        self.assertNotIn('abc', self.data)

        self.assertIn('b', self.data)
        self.assertIn('def', self.data['b'])
        self.assertIn('e', self.data['b']['def'])
        FormatedDict._rm(self.data, ['b', 'def', 'e'])
        self.assertNotIn('e', self.data['b']['def'])

    def test_cp(self):
        self.assertIn('abc', self.data)
        self.assertNotIn('abc_copy', self.data)
        FormatedDict._cp(self.data, ['abc'], ['abc_copy'])
        self.assertIn('abc', self.data)
        self.assertIn('abc_copy', self.data)

        self.assertIn('b', self.data)
        self.assertIn('def', self.data['b'])
        self.assertNotIn('b2', self.data)
        FormatedDict._cp(self.data, ['b', 'def'], ['b2', 'def_copy'])
        self.assertIn('b', self.data)
        self.assertIn('def', self.data['b'])
        self.assertIn('b2', self.data)
        self.assertIn('def_copy', self.data['b2'])

        self.assertIn('abc', self.data)
        self.assertNotIn('yc', self.data)
        FormatedDict._cp(self.data, ['abc', '!2'], ['yc'])
        self.assertIn('abc', self.data)
        self.assertIn('c', self.data['abc'])
        self.assertIn('yc', self.data)
        self.assertEqual('c', self.data['yc'])

    def test_mv(self):
        self.assertIn('abc', self.data)
        self.assertNotIn('abc_copy', self.data)
        FormatedDict._mv(self.data, ['abc'], ['abc_copy'])
        self.assertNotIn('abc', self.data)
        self.assertIn('abc_copy', self.data)
        self.assertIn('a', self.data['abc_copy'])
        self.assertIn('b', self.data['abc_copy'])
        self.assertIn('c', self.data['abc_copy'])

        self.assertIn('b', self.data)
        self.assertIn('def', self.data['b'])
        self.assertNotIn('b2', self.data)
        FormatedDict._mv(self.data, ['b', 'def'], ['b2', 'def_copy'])
        self.assertIn('b', self.data)
        self.assertNotIn('def', self.data['b'])
        self.assertIn('b2', self.data)
        self.assertIn('def_copy', self.data['b2'])

        self.assertIn('abc_copy', self.data)
        self.assertNotIn('yc', self.data)
        FormatedDict._mv(self.data, ['abc_copy', '!2'], ['yc'])
        self.assertIn('abc_copy', self.data)
        self.assertNotIn('c', self.data['abc_copy'])
        self.assertIn('yc', self.data)
        self.assertEqual('c', self.data['yc'])

    def test_get_path(self):
        self.assertEqual(self.data['a'],
                         FormatedDict._get_path(self.data, ['a']))
        self.assertEqual('c', FormatedDict._get_path(self.data, ['abc', '!2']))
        self.assertEqual('X2',
                         FormatedDict._get_path(self.data, ['z', '!1', 'x']))

    def test_init(self):
        fd = FormatedDict()
        self.assertEqual(fd.format, None)

        fd = FormatedDict(self.data)
        self.assertEqual(fd.format, None)
        self.assertEqual(fd['a'], self.data['a'])

        fd = FormatedDict(format="a=>aa")
        self.assertEqual(fd.format, "a=>aa")
        fd = FormatedDict(self.data, format="a=>aa")
        self.assertEqual(fd.format, "a=>aa")
        self.assertEqual(fd['a'], self.data['a'])

    def test_to_dict(self):
        self.assertIn('a',  self.data)
        self.assertIn('b',  self.data)
        fd = FormatedDict(self.data, format="a")
        new = fd.to_dict()
        self.assertIn('a', new)
        self.assertNotIn('b', new)
        self.assertIn('a',  self.data)
        self.assertIn('b',  self.data)

        self.assertNotIn('aa',  self.data)
        fd = FormatedDict(self.data, format="a=>aa")
        new = fd.to_dict()
        self.assertIn('aa', new)
        self.assertNotIn('aa',  self.data)

        self.assertIn('a',  self.data)
        fd = FormatedDict(self.data, format="-a")
        new = fd.to_dict()
        self.assertNotIn('a', new)
        self.assertIn('b', new)
        self.assertIn('z', new)
        self.assertIn('a',  self.data)


if __name__ == "__main__":
    main()
