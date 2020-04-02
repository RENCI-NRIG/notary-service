import json

import matplotlib.pyplot as plt
import numpy as np

# create empty data object for 4 graphs, 1000 samples, 4 measurements each
data = np.zeros((4, 1000, 4))

# data type
datatype = {'time-load': 0,
            'time-validate': 1,
            'check-empty': 2,
            'check-complete': 3
            }

# Load data into data object
graphname = {'one-by-two': 0,
             'three-by-three': 1,
             'five-by-five': 2,
             'seven-by-seven': 3
             }

for gn in graphname:
    print('-----', gn, '-----')
    filename = 'load-' + gn + '.graphml.json'
    print('Data from:', filename)
    with open('files/' + filename) as json_file:
        json_data = json.load(json_file)
    json_file.close()
    for i in range(len(json_data['measurement'])):
        data[graphname[gn], i, datatype['time-load']] = json_data['measurement'][i]['time_load']
        data[graphname[gn], i, datatype['time-validate']] = json_data['measurement'][i]['time_validate']
    print('  - load time(average):',
          np.average(data[graphname[gn], range(len(json_data['measurement'])), datatype['time-load']]))
    print('  - validate time(average):',
          np.average(data[graphname[gn], range(len(json_data['measurement'])), datatype['time-validate']]))

    filename = 'check-false-' + gn + '.graphml.json'
    print('Data from:', filename)
    with open('files/' + filename) as json_file:
        json_data = json.load(json_file)
    json_file.close()
    for i in range(len(json_data['measurement'])):
        data[graphname[gn], i, datatype['check-empty']] = json_data['measurement'][i]['time_check']
    print('  - check empty time(average):',
          np.average(data[graphname[gn], range(len(json_data['measurement'])), datatype['check-empty']]))

    filename = 'check-true-' + gn + '.graphml.json'
    print('Data from:', filename)
    with open('files/' + filename) as json_file:
        json_data = json.load(json_file)
    json_file.close()
    for i in range(len(json_data['measurement'])):
        data[graphname[gn], i, datatype['check-complete']] = json_data['measurement'][i]['time_check']
    print('  - check complete time(average):',
          np.average(data[graphname[gn], range(len(json_data['measurement'])), datatype['check-complete']]))

a1 = data[graphname['one-by-two'], :, datatype['time-load']]
a2 = data[graphname['one-by-two'], :, datatype['time-validate']]
a3 = data[graphname['one-by-two'], :, datatype['check-empty']]
a4 = data[graphname['one-by-two'], :, datatype['check-complete']]

b1 = data[graphname['three-by-three'], :, datatype['time-load']]
b2 = data[graphname['three-by-three'], :, datatype['time-validate']]
b3 = data[graphname['three-by-three'], :, datatype['check-empty']]
b4 = data[graphname['three-by-three'], :, datatype['check-complete']]

c1 = data[graphname['five-by-five'], :, datatype['time-load']]
c2 = data[graphname['five-by-five'], :, datatype['time-validate']]
c3 = data[graphname['five-by-five'], :, datatype['check-empty']]
c4 = data[graphname['five-by-five'], :, datatype['check-complete']]

d1 = data[graphname['seven-by-seven'], :, datatype['time-load']]
d2 = data[graphname['seven-by-seven'], :, datatype['time-validate']]
d3 = data[graphname['seven-by-seven'], :, datatype['check-empty']]
d4 = data[graphname['seven-by-seven'], :, datatype['check-complete']]

# Summary Table
print("{:<15} {:<15} {:<15} {:<15} {:<15}".format('Workflow', 'Load', 'Validate', 'Check empty', 'Check complete'))
for gn in graphname:
    print("{:<15} ".format(gn), end='', flush=True)
    for dt in datatype:
        val = round(np.average(data[graphname[gn], :, datatype[dt]]), 6)
        print("{:<15} ".format(val), end='', flush=True)
    print()

# Plots

kwargs = dict(alpha=0.5, bins=100, density=True, stacked=True)

# load times
plt.hist(a1, **kwargs, color='dodgerblue',
         label='1x2 (avg: ' + str(round(np.average(a1), 4)) + ' s)')
plt.hist(b1, **kwargs, color='orange',
         label='3x3 (avg: ' + str(round(np.average(b1), 4)) + ' s)')
plt.hist(c1, **kwargs, color='deeppink',
         label='5x5 (avg: ' + str(round(np.average(c1), 4)) + ' s)')
plt.hist(d1, **kwargs, color='green',
         label='7x7 (avg: ' + str(round(np.average(d1), 4)) + ' s)')

plt.title('Load workflow from GraphML file: time (s)')
plt.xlim(0.0, 0.05)

# validate times
# plt.hist(a2, **kwargs, color='dodgerblue',
#          label='1x2 (avg: ' + str(round(np.average(a2), 4)) + ' s)')
# plt.hist(b2, **kwargs, color='orange',
#          label='3x3 (avg: ' + str(round(np.average(b2), 4)) + ' s)')
# plt.hist(c2, **kwargs, color='deeppink',
#          label='5x5 (avg: ' + str(round(np.average(c2), 4)) + ' s)')
# plt.hist(d2, **kwargs, color='green',
#          label='7x7 (avg: ' + str(round(np.average(d2), 4)) + ' s)')
#
# plt.title('Validate workflow integrity: time (s)')
#
# plt.ylim(0.0, 3.0)


# check empty workflow
# plt.hist(a3, **kwargs, color='dodgerblue',
#          label='1x2 (avg: ' + str(round(np.average(a3), 4)) + ' s)')
# plt.hist(b3, **kwargs, color='orange',
#          label='3x3 (avg: ' + str(round(np.average(b3), 4)) + ' s)')
# plt.hist(c3, **kwargs, color='deeppink',
#          label='5x5 (avg: ' + str(round(np.average(c3), 4)) + ' s)')
# plt.hist(d3, **kwargs, color='green',
#          label='7x7 (avg: ' + str(round(np.average(d3), 4)) + ' s)')
#
# plt.title('Check workflow - empty: time (s)')
# plt.xlim(0.0, 0.35)
# plt.ylim(0.0, 100)


# check empty workflow
# plt.hist(a4, **kwargs, color='dodgerblue',
#          label='1x2 (avg: ' + str(round(np.average(a4), 4)) + ' s)')
# plt.hist(b4, **kwargs, color='orange',
#          label='3x3 (avg: ' + str(round(np.average(b4), 4)) + ' s)')
# plt.hist(c4, **kwargs, color='deeppink',
#          label='5x5 (avg: ' + str(round(np.average(c4), 4)) + ' s)')
# plt.hist(d4, **kwargs, color='green',
#          label='7x7 (avg: ' + str(round(np.average(d4), 4)) + ' s)')
#
# plt.title('Check workflow - complete: time (s)')
# plt.xlim(0.0, 11.5)
# plt.ylim(0.0, 10)

plt.legend()
plt.show()

# Additional graph which demonstrates the additive time issue found in graph validation

# plt.title('Validation time per iteration in sequential order')
# plt.plot(d2, color='green')
# plt.show()
