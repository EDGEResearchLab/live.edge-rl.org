
def filter_dict(dict_value, keys_to_remove):
    for key in dict_value.keys():
        if key in keys_to_remove:
            del dict_value[key]
    return dict_value
