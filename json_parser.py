import json
import urllib
from pprint import pformat
from urllib.request import urlopen
import math
import logging as log


def change_to_radians(val_in_degrees):
    """Zmienia wartosc w stopniach na radiany i ja zwraca"""
    return val_in_degrees * math.pi / 180.


class JsonParser:
    """Pomocnicza klasa do parsowania plikow JSON"""

    def __init__(self, posts_url, users_url, log_filename='logs.log'):
        """Wczytanie danych z adresow i zapisanie ich do pol skladowych klasy"""

        # Stworzenie wlasnego loggera
        log.basicConfig(filename=log_filename, level=log.INFO, filemode='w', format='%(message)s')

        try:
            # users
            json_url_users = urlopen(users_url)
            # posts
            json_url_posts = urlopen(posts_url)

            self.users_data = json.loads(json_url_users.read())
            self.posts_data = json.loads(json_url_posts.read())
        except ValueError:
            log.error("Nieznany typ URLa\n")

        except urllib.error.HTTPError as e:
            log.error("Błędny URL, powód: {0}, kod: {1}\n".format(e.reason, e.code))

        except Exception:
            log.error("Błędny URL\n")

    def join_json_files(self):
        """Laczy informacje o postach i uzytkownikach, zwracajac polaczone dane"""

        try:
            # merged_data = users_data + posts_data
            merged_data = self.users_data
        except AttributeError:
            error_string = "Brak danych użytkowników - źle pobrane dane."
            log.error(error_string)
            return error_string

        # stworzenie nowego klucza na posty o nazwie 'posts'
        for count, user in enumerate(merged_data):
            merged_data[count]['posts'] = []

        for post in self.posts_data:
            for count, user in enumerate(self.users_data):
                if user.get('id') == post.get('userId'):
                    post_dict = post.copy()
                    post_dict.pop('userId', None)
                    merged_data[count]['posts'].append(post_dict)
        return merged_data

    @staticmethod
    def list_of_strings(merged):
        """Liczy liczbe postow uzytkownika i zwraca stringa z policzonymi danymi"""
        string_list = []
        try:
            for user in merged:
                string_list.append("{0} napisał(a) {1} postów.".format(user['username'], len(user['posts'])))
            return string_list
        except TypeError:
            return "Brak danych - obiekt typu NoneType nie jest iterowalny."

    def list_of_duplicates(self):
        """Zwraca liste zduplikowanych tytulow postow"""
        seen = {}
        duplicates = []
        try:
            posts = self.posts_data
        except AttributeError:
            return "Brak danych o postach - źle pobrane dane."

        for post in self.posts_data:
            title = post.get('title')
            if title not in seen:
                seen[title] = 1
            else:
                if seen[title] == 1:
                    duplicates.append(title)
                seen[title] += 1
        if len(duplicates) == 0:
            log.info(pformat("Tytuły postów są unikalne - brak duplikatów."))
        log.info('Zwrócona lista:')
        return duplicates

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Liczy dystans w kilometrach pomiedzy dwoma punktami na mapie wedle formuly Haversine i zwraca go"""
        earth_radius = 6371e3  # promien Ziemi
        try:
            lat1 = float(lat1)
            lat2 = float(lat2)
            lon1 = float(lon1)
            lon2 = float(lon2)
        except ValueError:
            return "Błąd konwersji do float."

        fi1 = change_to_radians(lat1)  # zmiana na radiany
        fi2 = change_to_radians(lat2)
        delta_fi = change_to_radians(lat2 - lat1)
        delta_lambda = change_to_radians(lon2 - lon1)
        a = math.sin(delta_fi / 2.) * math.sin(delta_fi / 2.) + math.cos(fi1) * math.cos(fi2) * math.sin(
            delta_lambda / 2.) * math.sin(delta_lambda / 2.)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1. - a))
        distance = earth_radius * c
        return distance / 1000.  # wynik zwracamy w kilometrach

    def find_nearest_neighbour(self):
        """Konstruuje slownik z informacjami o wzajemnie najblizszych sasiadach i zwraca go"""
        connections = {}  # ostateczny dict z informacjami o sasiadach
        try:
            users = self.users_data
        except AttributeError:
            return "Brak danych użytkowników - źle pobrane dane."

        for user in self.users_data:
            temp_dict = {}  # pomocniczy dict do odpowiedniego sformatowania ostatecznego dicta
            nearest_neighbour = {}  # pomocniczy dict sasaida zawierajacy id i dystans do najblizszego sasiada
            user_id = user.get('id')
            name = user.get('name')
            flag = True
            for user2 in self.users_data:
                user2_id = user2.get('id')
                if user_id == user2_id:
                    continue  # omijamy porownanie dwoch takich samych osob
                else:
                    user_geo = user.get('address').get('geo')  # pierwsza osoba
                    user2_geo = user2.get('address').get('geo')  # druga osoba

                    lat1 = user_geo.get('lat')  # dlugosci i szerokosci geograficzne
                    lat2 = user2_geo.get('lat')
                    lng1 = user_geo.get('lng')
                    lng2 = user2_geo.get('lng')

                    distance = self.calculate_distance(lat1, lng1, lat2, lng2)  # policzenie dystansu
                    neighbour_name = user2.get('name')
                    if flag:
                        # zawartosc wykona sie tylko raz dla kazdej osoby
                        nearest_neighbour['neighbourId'] = user2_id
                        nearest_neighbour['neighbourName'] = neighbour_name
                        nearest_neighbour['distance'] = round(distance, 2)
                        temp_dict['name'] = name
                        temp_dict['neighbour'] = nearest_neighbour
                        flag = False
                    else:
                        if distance < float(nearest_neighbour.get('distance')):
                            nearest_neighbour['neighbourId'] = user2_id
                            nearest_neighbour['neighbourName'] = neighbour_name
                            nearest_neighbour['distance'] = round(distance, 2)
                            temp_dict['name'] = name
                            temp_dict['neighbour'] = nearest_neighbour
            connections[user_id] = temp_dict
            neighbour = temp_dict.get('neighbour')
            log.info(
                "Użytkownik:\n\tId:{0}\n\tImię i nazwisko: {1}\n\t"
                "Najbliższy sąsiad:\n\t\tId: {2}\n\t\tImię i nazwisko: {3}\n\t\tDystans: {4} km".format(
                    user_id, name, neighbour.get('neighbourId'),
                    neighbour.get('neighbourName'), neighbour.get('distance')))
        log.info("\nSłownik z danymi:\n")
        return connections


if __name__ == "__main__":
    # podane adresy URL
    url_posts = "https://jsonplaceholder.typicode.com/posts"
    url_users = "https://jsonplaceholder.typicode.com/users"

    # konstrukcja obiektu
    parser = JsonParser(url_posts, url_users)

    # 1.
    log.info("1. Zapisanie do pliku 'joined_data.json' efektu połączenia plików\n")
    with open('joined_data.json', 'w', encoding='utf-8') as f:
        joined_data = parser.join_json_files()
        json.dump(joined_data, f, ensure_ascii=False, indent=4)
    f.close()

    # 2.
    log.info("\n\n2. Policzenie postów użytkowników i zwrócenie listy stringów:\n")
    log.info(pformat(parser.list_of_strings(joined_data)))

    # 3.
    log.info("\n\n3. Zwrócenie listy zduplikowanych tytułów postów:\n")
    log.info(pformat((parser.list_of_duplicates())))

    # 4.
    log.info(
        "\n\n4. Zapisanie informacji o wzajemnie najbliższych sąsiadach oraz zwrócenie słownika z tymi informacjami:\n")
    log.info(pformat((parser.find_nearest_neighbour())))
