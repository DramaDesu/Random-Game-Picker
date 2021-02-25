import ast
from itertools import chain

import kivy
from kivy.config import Config
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
import csv

import galaxy_library_export
import galaxy_library_export
import locale
import natsort
import os
import pathlib
import random
import shutil
import subprocess
import sys

import hashlib

import configparser

from win32api import GetSystemMetrics


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


Config.set('graphics', 'resizable', True)
Config.set('graphics', 'position', 'center')

# Get program data path to store GameDB.csv and params.ini
app_data_path = os.getenv('APPDATA') + '\\Local\\Random Game Picker'

# Check if def_path exists. Create if necessary
os.makedirs(app_data_path, exist_ok=True)

# Define params.ini pathfile
param_file_path = app_data_path + '\\params.ini'

config = configparser.ConfigParser()

# Check if params.ini exists. Create if necessary
if not os.path.exists(param_file_path):
    config['DEFAULT']['LANGUAGE'] = 'EN'
    config['DEFAULT']['HIDDEN_FLAG'] = 'False'

    config['DEFAULT']['EXCLUDED_TAGS'] = ''
    config['DEFAULT']['INCLUDED_TAGS'] = ''

    config['DEFAULT']['EXCLUDED_GENRES'] = ''
    config['DEFAULT']['INCLUDED_GENRES'] = ''

    config['DEFAULT']['EXCLUDED_THEMES'] = ''
    config['DEFAULT']['INCLUDED_THEMES'] = ''

    config.add_section('WINDOW')

    default_width = 1280
    default_height = 720

    default_window_x = GetSystemMetrics(0) / 2 - default_width / 2
    default_window_y = GetSystemMetrics(1) / 2 - default_height / 2

    config['WINDOW']['WIDTH'] = str(default_width)
    config['WINDOW']['HEIGHT'] = str(default_height)

    config['WINDOW']['X'] = str(int(default_window_x))
    config['WINDOW']['Y'] = str(int(default_window_y))

    config.add_section('DATA')

    config['DATA']['DATA_BASE_HASH'] = ''

    with open(param_file_path, 'w') as configfile:  # save
        config.write(configfile)

config.read(param_file_path)

global_lang = config['DEFAULT']['LANGUAGE']
hidden_checkbox_active = config['DEFAULT']['HIDDEN_FLAG'] == 'True'

current_tags_excluded = config['DEFAULT']['EXCLUDED_TAGS']
current_tags_included = config['DEFAULT']['INCLUDED_TAGS']

current_genres_excluded = config['DEFAULT']['EXCLUDED_GENRES']
current_genres_included = config['DEFAULT']['INCLUDED_GENRES']

current_themes_excluded = config['DEFAULT']['EXCLUDED_THEMES']
current_themes_included = config['DEFAULT']['INCLUDED_THEMES']

window_width = int(config['WINDOW']['WIDTH'])
window_height = int(config['WINDOW']['HEIGHT'])

window_x = int(config['WINDOW']['X'])
window_y = int(config['WINDOW']['Y'])


# Format tags for further use
def format_tags(tags):
    if tags:
        user_tags = []

        if '[' not in tags:
            user_tags.append(tags)
        else:
            user_tags = ast.literal_eval(tags)

    else:
        user_tags = []

    return user_tags


# Main class
class GameRandomPickerLayout(Widget):
    # import global variables
    global global_lang
    global hidden_checkbox_active
    global current_tags_excluded
    global current_tags_included

    game_data = {
        "title": 0,
        "summary": 1,
        "critics_score": 2,
        "developers": 3,
        "genres": 4,
        "publishers": 5,
        "release_date": 6,
        "themes": 7,
        "release_key": 9,
        "game_mins": 9,
        "tags": 10,
        "dlcs": 11,
        "is_hidden": 12,
        "background_image": 13,
        "square_icon": 14,
        "vertical_cover": 15,
        "platform_list": 16
    }

    # Define app formating based on window size
    element_sizes = {
        "header_fontsize": 46,
        "pretitle_fontsize": 20,
        "title_fontsize": 30,
        "checkbox_fontsize": 15,
        "pick_button_fontsize": 26,
        "view_button_fontsize": 20,
        "help_fontsize": 14,
        "about_fontsize": 14,
        "spinner_fontsize": 15,
        "hidden_text_size": (400, 20),
        "pretitle_textsize": (150, 20),
        "title_textsize": (464, 150),
        "exc_inc_text_fontsize": 18,
        "exc_inc_textsize": (500, 50),
        "exc_inc_input_fontsize": 18
    }

    cover_present = False

    font_latothin = "fonts/Lato-Thin.ttf"
    font_latoreg = "fonts/Lato-Regular.ttf"

    current_lang = global_lang

    include_hidden_games = hidden_checkbox_active
    pick_button_is_pressed = False
    picked_game_cover = "images/cover_placeholder_en.png"
    picked_game_title = ""
    picked_game_score = ""
    picked_game_link = ""
    picked_games = []

    tags_excluded = current_tags_excluded
    tags_included = current_tags_included

    genres_excluded = current_genres_excluded
    genres_included = current_genres_included

    themes_excluded = current_themes_excluded
    themes_included = current_themes_included

    def __init__(self, **kwargs):
        super(GameRandomPickerLayout, self).__init__(**kwargs)

        self.filter_dropdowns = {}

    # Behaviour when PICK A RANDOM GAME button is pressed
    def pick_button_pressed(self):
        # Set GOG Galaxy games database filepath
        game_db = app_data_path + '\\GameDB.csv'

        with open(game_db, 'r', encoding='utf-8') as csv_file:
            csv_reader = list(csv.reader(csv_file))

        self.picked_games.clear()

        for data in list(csv_reader)[1:]:
            self.picked_games.append(data)

        random.shuffle(self.picked_games)

        self.next_random_game()

    def next_random_game(self):
        # import global variables
        global current_tags_excluded
        global current_tags_included

        global current_genres_excluded
        global current_genres_included

        global current_themes_excluded
        global current_themes_included

        global hidden_checkbox_active

        if len(self.picked_games) == 0:
            return

        user_excl_tags = format_tags(current_tags_excluded)
        user_incl_tags = format_tags(current_tags_included)

        user_excl_genres = format_tags(current_genres_excluded)
        user_incl_genres = format_tags(current_genres_included)

        user_excl_themes = format_tags(current_themes_excluded)
        user_incl_themes = format_tags(current_themes_included)

        while len(self.picked_games) > 0:
            # Pick a random game
            chosen_row = self.picked_games.pop(0)

            current_title_value = chosen_row[self.game_data["title"]]

            is_hidden_value = chosen_row[self.game_data["is_hidden"]]
            is_hidden = is_hidden_value == "True"

            print("Picked game: ", current_title_value)
            print("Hidden status: ", is_hidden_value)

            current_game_cover = chosen_row[self.game_data["vertical_cover"]]

            # Skip a game if it doesn't have an icon image
            if not current_game_cover:
                continue

            # Skip a hidden game
            if is_hidden and not hidden_checkbox_active:
                continue

            current_game_user_tags = format_tags(chosen_row[self.game_data["tags"]])

            current_game_genres = format_tags(chosen_row[self.game_data["genres"]])
            current_game_themes = format_tags(chosen_row[self.game_data["themes"]])

            game_is_matched = True

            game_is_matched &= set(user_excl_tags).isdisjoint(current_game_user_tags)
            if len(user_incl_tags) > 0:
                game_is_matched &= not set(user_incl_tags).isdisjoint(current_game_user_tags)

            game_is_matched &= set(user_excl_genres).isdisjoint(current_game_genres)
            if len(user_incl_genres) > 0:
                game_is_matched &= not set(user_incl_genres).isdisjoint(current_game_genres)

            game_is_matched &= set(user_excl_themes).isdisjoint(current_game_themes)
            if len(user_incl_themes) > 0:
                game_is_matched &= not set(user_incl_themes).isdisjoint(current_game_themes)

            if game_is_matched:
                self.update_game_data(chosen_row)
                break

            # Check to exit the loop if there are no more games to pick
            if len(self.picked_games) == 0:
                print("There are no more games! Starting a new search loop\n")
                break

    def pick_next_game_button_pressed(self):
        self.next_random_game()

    # Update the main window with picked game data
    def update_game_data(self, data):
        self.picked_game_title = data[self.game_data["title"]]
        self.picked_game_score = data[self.game_data["critics_score"]]
        self.picked_game_link = data[self.game_data["platform_list"]][2:].split("'")[0]
        if data[self.game_data["vertical_cover"]]:
            self.picked_game_cover = data[self.game_data["vertical_cover"]]
            self.cover_present = True
        else:
            self.picked_game_cover = self.localization[self.current_lang]["default_cover"]
            self.cover_present = False

        self.update_game_title(self.picked_game_title)
        self.update_game_score(self.picked_game_score)
        self.update_game_cover(self.picked_game_cover)
        self.update_game_genres(data[self.game_data["genres"]])
        self.update_game_themes(data[self.game_data["themes"]])
        self.update_game_tags(data[self.game_data["tags"]])
        self.pick_button_is_pressed = True

    def update_game_title(self, game_title):
        self.ids.game_title.text = game_title

    def update_game_score(self, game_score):
        result_str = ''
        if len(game_score) > 0:
            result_str = game_score + '/100'

        self.ids.game_score.text = result_str

    def update_game_genres(self, game_genres):
        self.ids.game_genres.text = ", ".join(str(x) for x in format_tags(game_genres))

    def update_game_themes(self, game_themes):
        self.ids.game_themes.text = ", ".join(str(x) for x in format_tags(game_themes))

    def update_game_tags(self, game_tags):
        self.ids.game_tags.text = ", ".join(str(x) for x in format_tags(game_tags))

    def update_game_cover(self, game_cover):
        self.ids.cover_image.source = game_cover

    # Update localization
    def update_program_localization(self):
        pass

    # Behaviour when the VIEW GAME IN GOG GALAXY button is pressed
    def view_button_pressed(self):
        if self.picked_game_link:
            subprocess.run("start goggalaxy://openGameView/" + self.picked_game_link, shell=True)

    def set_program_language(self, language):
        global global_lang

        lang_code = language

        if self.current_lang != lang_code:
            self.current_lang = lang_code
            global_lang = lang_code
            self.update_program_localization()

    def hidden_checkbox(self, instance, value):
        global hidden_checkbox_active
        hidden_checkbox_active = value
        self.include_hidden_games = value

    def update_excluded_tags(self, tags):
        global current_tags_excluded
        self.tags_excluded = tags
        current_tags_excluded = self.tags_excluded

    def update_included_tags(self, tags):
        global current_tags_included
        self.tags_included = tags
        current_tags_included = self.tags_included

    def update_excluded_genres(self, tags):
        global current_genres_excluded
        self.genres_excluded = tags
        current_genres_excluded = self.genres_excluded

    def update_included_genres(self, tags):
        global current_genres_included
        self.genres_included = tags
        current_genres_included = self.genres_included

    def update_excluded_themes(self, tags):
        global current_themes_excluded
        self.themes_excluded = tags
        current_themes_excluded = self.themes_excluded

    def update_included_themes(self, tags):
        global current_themes_included
        self.themes_included = tags
        current_themes_included = self.themes_included

    def init(self):
        drop_down_container = self.ids.drop_down_container

        if drop_down_container:
            # Set GOG Galaxy games database filepath
            game_db = app_data_path + '\\GameDB.csv'

            with open(game_db, 'r', encoding='utf-8') as csv_file:
                csv_reader = list(csv.reader(csv_file))

            all_game_tags = set()
            all_game_genres = set()
            all_game_themes = set()

            for data in list(csv_reader)[1:]:
                game_tags = format_tags(data[self.game_data["tags"]])
                for tag in game_tags:
                    all_game_tags.add(tag)

                game_genres = format_tags(data[self.game_data["genres"]])
                for genre in game_genres:
                    all_game_genres.add(genre)

                game_themes = format_tags(data[self.game_data["themes"]])
                for theme in game_themes:
                    all_game_themes.add(theme)

            all_game_tags = sorted(all_game_tags)
            all_game_genres = sorted(all_game_genres)
            all_game_themes = sorted(all_game_themes)

            global current_tags_excluded
            global current_tags_included

            global current_genres_excluded
            global current_genres_included

            global current_themes_excluded
            global current_themes_included

            if len(all_game_tags) > 0:
                self.make_filter_dropdown(self.ids.exclude_tags_dropdown, all_game_tags,
                                          format_tags(current_tags_excluded), self.update_excluded_tags)
                self.make_filter_dropdown(self.ids.include_tags_dropdown, all_game_tags,
                                          format_tags(current_tags_included), self.update_included_tags)

            if len(all_game_genres) > 0:
                self.make_filter_dropdown(self.ids.exclude_genres_dropdown, all_game_genres,
                                          format_tags(current_genres_excluded),self.update_excluded_genres)
                self.make_filter_dropdown(self.ids.include_genres_dropdown, all_game_genres,
                                          format_tags(current_genres_included), self.update_included_genres)

            if len(all_game_themes) > 0:
                self.make_filter_dropdown(self.ids.exclude_themes_dropdown, all_game_themes,
                                          format_tags(current_themes_excluded), self.update_excluded_themes)
                self.make_filter_dropdown(self.ids.include_themes_dropdown, all_game_themes,
                                          format_tags(current_themes_included), self.update_included_themes)

    def get_values_from_filter_dropdown(self, button):
        dropdown_callback = list(self.filter_dropdowns[button])
        dropdown = dropdown_callback[0]

        out_values = []

        for child_box in dropdown.children:
            for child in child_box.children:
                if child.state == 'down':
                    out_values.append(child.text)

        return out_values

    def get_exclude_tags_values(self):
        return self.get_values_from_filter_dropdown(self.ids.exclude_tags_dropdown)

    def get_include_tags_values(self):
        return self.get_values_from_filter_dropdown(self.ids.include_tags_dropdown)

    def get_exclude_genres_values(self):
        return self.get_values_from_filter_dropdown(self.ids.exclude_genres_dropdown)

    def get_include_genres_values(self):
        return self.get_values_from_filter_dropdown(self.ids.include_genres_dropdown)

    def get_exclude_themes_values(self):
        return self.get_values_from_filter_dropdown(self.ids.exclude_themes_dropdown)

    def get_include_themes_values(self):
        return self.get_values_from_filter_dropdown(self.ids.include_themes_dropdown)

    def make_filter_dropdown(self, button, data, init_data, callback):

        current_buttons = []

        current_dropdown = DropDown(dismiss_on_select=False)
        for tag in data:
            # When adding widgets, we need to specify the height manually
            # (disabling the size_hint_y) so the dropdown can calculate
            # the area it needs.

            btn = ToggleButton(text='%s' % tag, size_hint_y=None, height=25)

            if tag in init_data:
                btn.state = 'down'

            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda in_btn: self.update_multiselect_tags(in_btn, current_dropdown, current_buttons,
                                                                            callback))

            current_buttons.append(btn)

            # then add the button inside the dropdown
            current_dropdown.add_widget(btn)

        # button.bind(on_press=current_dropdown.open)

        button.bind(on_release=lambda button_instance: current_dropdown.open(button_instance))

        # one last thing, listen for the selection in the dropdown list and
        # assign the data to the button text.
        current_dropdown.bind(on_select=lambda instance, x: setattr(button, 'text', x))

        if len(init_data) > 0:
            current_dropdown.select('None')
            tags_text = self.get_text_from_dropdown_multiselect(current_buttons)
            if tags_text:
                current_dropdown.select(tags_text)

        self.filter_dropdowns[button] = {current_dropdown, callback}

    def clear_all_filters(self):
        for button in self.filter_dropdowns:
            self.clear_filter(button)

    def clear_filter(self, button):
        dropdown_callback = list(self.filter_dropdowns[button])

        dropdown = dropdown_callback[0]
        callback = dropdown_callback[1]

        dropdown.select('None')
        for child_box in dropdown.children:
            for child in child_box.children:
                child.state = 'normal'

        callback('')

    def clear_filters_button_pressed(self):
        self.clear_all_filters()

    @staticmethod
    def get_text_from_dropdown_multiselect(buttons):
        tags_text = ''
        for btn in buttons:
            if btn.state == 'down':
                tags_text = tags_text + btn.text + ', '

        if tags_text and tags_text.endswith(', '):
            tags_text = tags_text[:-2]

        return tags_text

    def update_multiselect_tags(self, button, dropdown, buttons, callback):
        dropdown.select('None')
        tags_text = self.get_text_from_dropdown_multiselect(buttons)
        if tags_text:
            dropdown.select(tags_text)

        callback(tags_text)


def create_or_update_data_base():
    gog_data_base_location = os.getenv('PROGRAMDATA') + '\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db'

    cached_db_hash = config['DATA']['DATA_BASE_HASH']
    current_db_hash = str(md5(gog_data_base_location))

    if cached_db_hash != current_db_hash:
        config['DATA']['DATA_BASE_HASH'] = current_db_hash

        # Create cvs file for user library
        sys.argv = ['galaxy_library_export.py', '-d=,', '--py-lists', '--all']
        galaxy_library_export.main()


class RandomGamePicker(App):
    global window_height
    global window_width

    # Set the program main window parameters
    def __init__(self, **kwargs):
        super(RandomGamePicker, self).__init__(**kwargs)
        self.layout = None

    def build(self):
        create_or_update_data_base()

        Window.size = (window_width, window_height)

        Window.left = window_x
        Window.top = window_y

        self.icon = 'images/app.ico'
        self.title = "Random Game Picker"

        self.layout = GameRandomPickerLayout()

        self.layout.init()

        return self.layout

    # Behaviour while the program is closing
    def on_stop(self):
        global global_lang
        global hidden_checkbox_active
        global param_file_path
        global current_tags_excluded
        global current_tags_included
        global current_genres_excluded
        global current_genres_included
        global current_themes_excluded
        global current_themes_included

        current_tags_excluded = str(self.layout.get_exclude_tags_values())
        current_tags_included = str(self.layout.get_include_tags_values())

        current_genres_excluded = str(self.layout.get_exclude_genres_values())
        current_genres_included = str(self.layout.get_include_genres_values())

        current_themes_excluded = str(self.layout.get_exclude_themes_values())
        current_themes_included = str(self.layout.get_include_themes_values())

        config['DEFAULT']['LANGUAGE'] = global_lang
        config['DEFAULT']['HIDDEN_FLAG'] = str(hidden_checkbox_active)

        config['DEFAULT']['EXCLUDED_TAGS'] = current_tags_excluded
        config['DEFAULT']['INCLUDED_TAGS'] = current_tags_included

        config['DEFAULT']['EXCLUDED_GENRES'] = current_genres_excluded
        config['DEFAULT']['INCLUDED_GENRES'] = current_genres_included

        config['DEFAULT']['EXCLUDED_THEMES'] = current_themes_excluded
        config['DEFAULT']['INCLUDED_THEMES'] = current_themes_included

        config['WINDOW']['WIDTH'] = str(Window.size[0])
        config['WINDOW']['HEIGHT'] = str(Window.size[1])

        config['WINDOW']['X'] = str(int(Window.left))
        config['WINDOW']['Y'] = str(int(Window.top))

        with open(param_file_path, 'w') as f:  # save
            config.write(f)


if __name__ == '__main__':
    RandomGamePicker().run()
