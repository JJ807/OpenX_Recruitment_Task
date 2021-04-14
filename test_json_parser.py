import json_parser
import unittest


class JsonParserTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nThe start of the test")

    @classmethod
    def tearDownClass(cls):
        print("\nThe end of the test")

    def setUp(self):
        self.log_filename = 'test_logs.log'
        self.parser = json_parser.JsonParser("https://jsonplaceholder.typicode.com/posts",
                                             "https://jsonplaceholder.typicode.com/users", self.log_filename)

    def tearDown(self):
        pass

    def test_change_to_radians(self):
        self.assertEqual(json_parser.change_to_radians(180), json_parser.math.pi)

    def test_init(self):
        file = open(self.log_filename, "r+")
        file.truncate(0)
        file.close()

        json_parser.JsonParser('', '', self.log_filename)
        with open(self.log_filename, 'r+') as logfile:
            log = logfile.readline()
            self.assertTrue("Nieznany typ URLa" in log)

            json_parser.JsonParser('https://jsonplaceholder.', 'https://jsonplaceholder.', self.log_filename)
            next(logfile)
            log = logfile.readline()
            self.assertTrue("Błędny URL" in log)

            json_parser.JsonParser('https://jsonplaceholder.typicode.co', 'https://jsonplaceholder.typicode.co',
                                   self.log_filename)
            next(logfile)
            log = logfile.readline()
            self.assertTrue("Błędny URL, powód: Forbidden" in log)
        logfile.close()

    def test_join_json_files(self):
        temp = json_parser.JsonParser('', '', self.log_filename)
        self.assertEqual(temp.join_json_files(), "Brak danych użytkowników - źle pobrane dane.")

    def test_list_of_strings(self):
        merged = self.parser.join_json_files()
        self.assertEqual(len(merged), len(self.parser.list_of_strings(merged)))
        merged = None
        self.assertEqual("Brak danych - obiekt typu NoneType nie jest iterowalny.", self.parser.list_of_strings(merged))

    def test_list_of_duplicates(self):
        # 1
        self.assertEqual(len(self.parser.list_of_duplicates()), 0)
        temp = json_parser.JsonParser('', '', self.log_filename)
        # 2
        self.assertEqual(temp.list_of_duplicates(), "Brak danych o postach - źle pobrane dane.")
        # 3
        temp.posts_data = json_parser.json.loads('[{"title": "sth"}, {"title": "sth"}]')
        duplicates = temp.list_of_duplicates()
        self.assertEqual(len(duplicates), 1)
        # 4
        self.assertEqual(duplicates[0], 'sth')

    def test_calculate_distance(self):
        self.assertEqual(self.parser.calculate_distance('', '', '', ''), "Błąd konwersji do float.")

    def test_find_nearest_neighbour(self):
        # 1
        temp = json_parser.JsonParser('', '', self.log_filename)
        self.assertEqual(temp.find_nearest_neighbour(), "Brak danych użytkowników - źle pobrane dane.")
        # 2
        self.assertEqual(len(self.parser.find_nearest_neighbour()), 10)


if __name__ == "__main__":
    unittest.main()
