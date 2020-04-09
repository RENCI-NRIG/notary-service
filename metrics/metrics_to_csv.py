import json
import csv

# set path prefix to json data files
# path_prefix = 'files/10'
path_prefix = 'files/1000'

graphname = ['one-by-two',
             'three-by-three',
             'five-by-five',
             'seven-by-seven'
             ]

for graph in graphname:
    # open output CSV file
    csv_out = open(path_prefix + '/' + graph + '.csv', 'w')
    # create data object for combined data
    data_out = []

    # set index and uuid
    with open(path_prefix + '/uuid.json', 'r') as json_file:
        json_data = json.load(json_file)
    tmp_data = json_data['uuid']

    index = 1
    for row in tmp_data:
        uuid_index = {
            'index': index,
            'uuid': row
        }
        data_out.append(uuid_index)
        index += 1

    # add import and validate data
    with open(path_prefix + '/load-' + graph + '.graphml.json') as json_file:
        json_data = json.load(json_file)
    tmp_data = json_data['measurement']
    # assign data corresponding to matching uuid
    for r_tmp in tmp_data:
        for r_data in data_out:
            if r_tmp['uuid'] == r_data['uuid']:
                r_data['time_load'] = r_tmp['time_load']
                r_data['time_validate'] = r_tmp['time_validate']
                r_data['check_is_valid'] = r_tmp['is_valid']
                break

    # add check empty data
    with open(path_prefix + '/check-false-' + graph + '.graphml.json') as json_file:
        json_data = json.load(json_file)
    tmp_data = json_data['measurement']
    # assign data corresponding to matching uuid
    for r_tmp in tmp_data:
        for r_data in data_out:
            if r_tmp['uuid'] == r_data['uuid']:
                r_data['time_check_empty'] = r_tmp['time_check']
                r_data['check_is_complete_empty'] = r_tmp['is_complete']
                break

    # add check complete data
    with open(path_prefix + '/check-true-' + graph + '.graphml.json') as json_file:
        json_data = json.load(json_file)
    tmp_data = json_data['measurement']
    # assign data corresponding to matching uuid
    for r_tmp in tmp_data:
        for r_data in data_out:
            if r_tmp['uuid'] == r_data['uuid']:
                r_data['time_check_full'] = r_tmp['time_check']
                r_data['check_is_complete_full'] = r_tmp['is_complete']
                break

    print('Writing CSV data to file:', csv_out.name)
    csvwrite = csv.writer(csv_out)
    count = 0
    for row in data_out:
        if count == 0:
            csvwrite.writerow(row.keys())
        csvwrite.writerow(row.values())
        count += 1

    csv_out.close()
