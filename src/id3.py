"""
    authors:
    Joanna Sokolowska - https://github.com/jsokolowska
    Rafal Uzarowicz - https://github.com/RafalUzarowicz
"""

from numpy import log2
import pandas as pd
import numpy as np


class ID3:
    def __init__(self, dataset: pd.DataFrame = None, classification_attribute: str = None):
        self.use_ranges_in_numeric_attributes = True
        self.dataset = None
        self.classification_attribute = None
        self.tree = None
        self.classification_attribute_values = None
        self.is_attribute_numeric = None
        self.average_attribute_values_number = None
        self.attribute_range_dividers = {}
        if dataset is not None and classification_attribute is not None:
            self.initialize_algorithm(dataset, classification_attribute)
        else:
            raise ValueError("Wrong number of arguments!")

    def __str__(self):
        return "Classification values: " + str(self.classification_attribute_values) + "\nTree: " + str(self.tree)

    def initialize_algorithm(self, dataset: pd.DataFrame, classification_attribute: str) -> None:
        if dataset is None or classification_attribute is None:
            raise ValueError("Wrong arguments.")
        self.dataset = dataset
        self.classification_attribute = classification_attribute
        self.tree = None
        if self.classification_attribute not in self.dataset.columns:
            raise ValueError("Wrong classification attribute name!")
        self.classification_attribute_values = list(set(self.dataset[self.classification_attribute].to_list()))
        self.is_attribute_numeric = {}
        self.prepare_tree()

    def prepare_data(self) -> None:
        def is_number(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        self.classification_attribute_values = list(set(self.dataset[self.classification_attribute].to_list()))
        self.is_attribute_numeric = {}
        self.average_attribute_values_number = int(self.find_average_attribute_values_number())
        for val in list(self.dataset.columns):
            if all(is_number(n) for n in self.dataset[val]):
                self.is_attribute_numeric[val] = True
                self.dataset[val] = pd.to_numeric(self.dataset[val], errors='coerce')
            else:
                self.is_attribute_numeric[val] = False

        if self.use_ranges_in_numeric_attributes:
            for attribute in self.dataset.columns:
                if self.is_attribute_numeric[attribute] and attribute != self.classification_attribute:
                    minimum_attribute_value = self.dataset[attribute].min()
                    maximum_attribute_value = self.dataset[attribute].max()
                    self.attribute_range_dividers[attribute] = []
                    for i in range(1, self.average_attribute_values_number):
                        self.attribute_range_dividers[attribute].append(minimum_attribute_value+((maximum_attribute_value-minimum_attribute_value)*i/self.average_attribute_values_number))

    def entropy(self, data: pd.DataFrame) -> float:
        entropy = 0.0
        for val in self.classification_attribute_values:
            if len(data[data[self.classification_attribute] == val]) > 0:
                fraction = len(data[data[self.classification_attribute] == val]) / len(data)
                entropy += - fraction * log2(fraction)
        return entropy

    def find_average_attribute_values_number(self):
        sum_of_unique_attribute_values = 0.0
        counter = 0
        for key in self.dataset.columns:
            if not key == self.classification_attribute:
                sum_of_unique_attribute_values += len(self.dataset[key].unique())
                counter += 1
        if counter > 0:
            return sum_of_unique_attribute_values/counter
        else:
            raise ValueError("Empty dataset!")

    def find_pivot(self, data: pd.DataFrame, attribute: str) -> float:
        # average value for now
        if not self.is_attribute_numeric[attribute]:
            raise ValueError("Wrong type of attribute for average function.")
        values_list = data[attribute].to_list()
        if not len(values_list) > 0:
            raise ValueError("Empty dataset.")
        values_sum = 0.0
        for val in values_list:
            values_sum += val
        return values_sum / len(values_list)

    def gain(self, data: pd.DataFrame, attribute: str) -> float:
        if attribute not in self.dataset.columns or attribute == self.classification_attribute:
            raise ValueError("Wrong attribute for information gain!")
        info_gain = self.entropy(data)
        if self.is_attribute_numeric.get(attribute, None) is False:
            for val in data[attribute].unique():
                info_gain -= self.entropy(data[data[attribute] == val]) * len(data[data[attribute] == val]) / len(data)
        elif self.is_attribute_numeric.get(attribute, False) is True:
            if self.use_ranges_in_numeric_attributes:
                data[attribute] = pd.to_numeric(data[attribute], errors='coerce')
                info_gain -= self.entropy(data[data[attribute] <= self.attribute_range_dividers[attribute][0]]) * len(data[data[attribute] <= self.attribute_range_dividers[attribute][0]]) / len(data)
                for i in range(1, len(self.attribute_range_dividers[attribute])-1):
                    temp_data = data[data[attribute] <= self.attribute_range_dividers[attribute][i+1]].__deepcopy__()
                    temp_data = temp_data[temp_data[attribute] > self.attribute_range_dividers[attribute][i]].__deepcopy__()
                    info_gain -= self.entropy(temp_data) * len(temp_data) / len(data)
                info_gain -= self.entropy(data[data[attribute] > self.attribute_range_dividers[attribute][-1]]) * len(
                    data[data[attribute] > self.attribute_range_dividers[attribute][-1]]) / len(data)
            else:
                pivot = self.find_pivot(data, attribute)
                info_gain -= self.entropy(data[data[attribute] >= pivot]) * len(data[data[attribute] >= pivot]) / len(data)
                info_gain -= self.entropy(data[data[attribute] < pivot]) * len(data[data[attribute] < pivot]) / len(data)
        return info_gain

    def find_maximum_gain(self, data: pd.DataFrame) -> str:
        best_attr = ""
        best_gain = -1.0
        for key in data.columns:
            if not key == self.classification_attribute:
                current_gain = self.gain(data, key)
                if current_gain >= best_gain:
                    best_attr = key
                    best_gain = current_gain
        return best_attr

    def prepare_tree(self):
        all_attributes = list(self.dataset.columns)

        def build_tree(data: pd.DataFrame) -> {}:

            def end_conditions(end_val: list, curr_dataset: pd.DataFrame):
                if len(all_attributes) == 1:
                    values_counter = {k: 0 for k in self.classification_attribute_values}
                    for value in end_val:
                        values_counter[value] += 1
                    best_val = self.classification_attribute_values[0]
                    best_count = values_counter[best_val]
                    for value in end_val:
                        curr_count = values_counter[value]
                        if curr_count > best_count:
                            best_val = value
                            best_count = curr_count
                    return best_val

                first_val = end_val[0]

                if all(n == first_val for n in end_val):
                    return first_val

                return build_tree(curr_dataset)

            data = data[all_attributes]
            max_gain_att = self.find_maximum_gain(data)
            all_attributes.remove(max_gain_att)

            node = {max_gain_att: {}}

            if self.is_attribute_numeric[max_gain_att]:
                if self.use_ranges_in_numeric_attributes:
                    split_set = data[data[max_gain_att] <= self.attribute_range_dividers[max_gain_att][0]]
                    split_set = split_set.drop(columns=max_gain_att, axis=1)
                    if len(split_set) > 0:
                        end_values = list(split_set[self.classification_attribute])
                        node[max_gain_att][0] = end_conditions(end_values, split_set)
                    for i in range(1, len(self.attribute_range_dividers[max_gain_att])-1):
                        split_set = data[data[max_gain_att] <= self.attribute_range_dividers[max_gain_att][i+1]].__deepcopy__()
                        split_set = split_set[split_set[max_gain_att] > self.attribute_range_dividers[max_gain_att][i]].__deepcopy__()
                        split_set = split_set.drop(columns=max_gain_att, axis=1)
                        if len(split_set) > 0:
                            end_values = list(split_set[self.classification_attribute])
                            node[max_gain_att][i] = end_conditions(end_values, split_set)
                    split_set = data[data[max_gain_att] > self.attribute_range_dividers[max_gain_att][-1]]
                    split_set = split_set.drop(columns=max_gain_att, axis=1)
                    if len(split_set) > 0:
                        end_values = list(split_set[self.classification_attribute])
                        node[max_gain_att][len(self.attribute_range_dividers[max_gain_att])-1] = end_conditions(end_values, split_set)

                else:
                    node[max_gain_att]["pivot"] = self.find_pivot(data, max_gain_att)

                    # less than pivot
                    split_set = data[data[max_gain_att] < node[max_gain_att]["pivot"]]
                    split_set = split_set.drop(columns=max_gain_att, axis=1)
                    if len(split_set) > 0:
                        end_values = list(split_set[self.classification_attribute])
                        node[max_gain_att][0] = end_conditions(end_values, split_set)

                    # more than pivot
                    split_set = data[data[max_gain_att] >= node[max_gain_att]["pivot"]]
                    split_set = split_set.drop(columns=max_gain_att, axis=1)

                    end_values = list(split_set[self.classification_attribute])
                    node[max_gain_att][1] = end_conditions(end_values, split_set)
            else:
                for val in data[max_gain_att].unique():
                    split_set = data[data[max_gain_att] == val]
                    split_set = split_set.drop(columns=max_gain_att, axis=1)

                    end_values = list(split_set[self.classification_attribute])
                    node[max_gain_att][val] = end_conditions(end_values, split_set)

            return node

        def get_misclasified() -> pd.DataFrame:
            predictions = self.predict(self.dataset)
            col_name = "predictions"
            self.dataset[col_name] = predictions
            mis = pd.DataFrame()
            for i, row in self.dataset.iterrows():
                target = self.dataset.columns[self.dataset.columns.get_loc(self.classification_attribute)]
                prediction = self.dataset.columns[self.dataset.columns.get_loc(col_name)]
                if row[target] != row[prediction]:
                    mis.append(row)
            self.dataset = self.dataset.drop(columns=col_name)
            return mis

        msk = np.random.rand(len(self.dataset)) < 0.4
        window = self.dataset[msk].__deepcopy__()
        nr_misses = 1
        self.tree = None

        while nr_misses > 0:
            self.prepare_data()
            self.tree = build_tree(window)
            misses = get_misclasified()
            nr_misses = len(misses)
            if nr_misses:
                misses = misses.iloc[:, :-1]
                window = window.append(misses)

    def predict(self, dataset: pd.DataFrame) -> []:
        predictions = []
        for index, row in dataset.iterrows():
            is_found = True
            cut_tree = self.tree
            while type(cut_tree) is dict:
                key_list = list(cut_tree.keys())
                attribute = key_list[0]
                if self.is_attribute_numeric.get(attribute, False):
                    if self.use_ranges_in_numeric_attributes:
                        if row[attribute] > self.attribute_range_dividers[attribute][-1]:
                            cut_tree = cut_tree[attribute][len(self.attribute_range_dividers[attribute])-1]
                        else:
                            for i in range(len(self.attribute_range_dividers[attribute])):
                                if row[attribute] <= self.attribute_range_dividers[attribute][i]:
                                    if i in cut_tree[attribute].keys():
                                        cut_tree = cut_tree[attribute][i]
                                        break
                                    is_found = False
                    else:
                        if row[attribute] >= cut_tree[attribute]["pivot"]:
                            cut_tree = cut_tree[attribute][1]
                        else:
                            cut_tree = cut_tree[attribute][0]
                else:
                    if row[attribute] not in cut_tree[attribute].keys():
                        is_found = False
                        break
                    cut_tree = cut_tree[attribute][row[attribute]]
            if is_found:
                predictions.append(cut_tree)
            else:
                predictions.append(None)
        return predictions


def count_good(data_frame: pd.DataFrame, classification_attribute: str) -> int:
    count = 0
    for i, row in data_frame.iterrows():
        if row[classification_attribute] == row["pred"]:
            count += 1
    return count
