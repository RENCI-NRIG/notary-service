import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from metrics_neo4j import create_graph_from_file, delete_workflow_by_uuid, \
    delete_all_nodes, is_workflow_complete, set_workflow_nodes_as_completed, create_neo4j_indices

load_dotenv('env.python')


# generate list of uuids
def generate_uuid_list(number_of_uuids):
    """
    Parameters
    ----------
    number_of_uuids - number of unique IDs to create

    Returns
    -------
    no return value

    """
    uuid_list = []
    for i in range(int(number_of_uuids)):
        uuid_list.append(str(uuid.uuid4()))
    file = open("files/uuid.json", "w")
    file.write(json.dumps({"uuid": uuid_list}, indent=4))
    file.close()
    print("File with", str(number_of_uuids), "unique IDs has been created as: 'files/uuid.json'")


# load neo4j graph by uuid
def load_neo4j_graph(path_to_graph: str):
    print("Generate import metrics for:", path_to_graph)
    with open('files/uuid.json', encoding='utf-8') as f:
        json_data = json.loads(f.read())
    data = {
        'graph': os.path.basename(path_to_graph),
        'count': len(json_data['uuid'])
    }
    tt_c = 0
    tt_v = 0
    g_mets = []
    print('  - Running with', len(json_data['uuid']), 'iterations:')
    for item in json_data['uuid']:
        graph_id, is_complete, tc, tv = create_graph_from_file(path_to_graph, item)
        print('.', end='', flush=True)
        tt_c = tt_c + tc
        tt_v = tt_v + tv
        g_mets.append({
            'uuid': graph_id,
            'time_load': tc,
            'time_validate': tv,
            'time_units': 'seconds',
            'is_valid': is_complete
        })

    print('')
    data['metrics_load'] = {'total': tt_c, 'average': tt_c / len(json_data['uuid']), 'units': 'seconds'}
    data['metrics_validate'] = {'total': tt_v, 'average': tt_v / len(json_data['uuid']), 'units': 'seconds'}
    print(json.dumps(data, indent=4))
    data['measurement'] = g_mets
    # output datafile
    file = open("files/load-" + str(os.path.basename(path_to_graph) + '.json'), "w")
    file.write(json.dumps(data, indent=4))

    file.close()
    print("File with load/validate metrics saved as:", file.name)


# check graph for completeness by uuid
def check_graph_for_workflow_completeness(path_to_graph: str):
    print("Check for workflow completeness using graph:", path_to_graph)
    with open('files/uuid.json', encoding='utf-8') as f:
        json_data = json.loads(f.read())
    data = {
        'graph': os.path.basename(path_to_graph),
        'count': len(json_data['uuid'])
    }
    tt_c = 0
    g_mets = []
    print('  - Running with', len(json_data['uuid']), 'iterations:')
    for item in json_data['uuid']:
        graph_id, is_complete, tc = is_workflow_complete(item)
        print('.', end='', flush=True)
        tt_c = tt_c + tc
        g_mets.append({
            'uuid': graph_id,
            'time_check': tc,
            'time_units': 'seconds',
            'is_complete': is_complete
        })

    print('')
    data['metrics_check'] = {'total': tt_c, 'average': tt_c / len(json_data['uuid']), 'units': 'seconds'}
    print(json.dumps(data, indent=4))
    data['measurement'] = g_mets
    # output datafile
    if str(g_mets[0]['is_complete']) == 'True':
        file = open("files/check-true-" + str(os.path.basename(path_to_graph) + '.json'), "w")
    else:
        file = open("files/check-false-" + str(os.path.basename(path_to_graph) + '.json'), "w")
    file.write(json.dumps(data, indent=4))
    file.close()
    print("File with load/validate metrics saved as:", file.name)


# delete neo4j graph by uuid
def set_workflow_as_completed():
    print("Set all workflow nodes as completed")
    with open('files/uuid.json', encoding='utf-8') as f:
        json_data = json.loads(f.read())
    for item in json_data['uuid']:
        print(item)
        set_workflow_nodes_as_completed(item)


# delete neo4j graph by uuid
def remove_all_neo4j_graph():
    print("Remove all Neo4j graphs")
    with open('files/uuid.json', encoding='utf-8') as f:
        json_data = json.loads(f.read())
    for item in json_data['uuid']:
        print(item)
        delete_workflow_by_uuid(item)
    delete_all_nodes()


# main
def main(generateids: int, importgraph: str, removegraph: bool, checkworkflow: str, completeall: str, createindices: bool):
    if isinstance(generateids, int):
        generate_uuid_list(generateids)
    if isinstance(importgraph, str):
        load_neo4j_graph(importgraph)
    if removegraph:
        remove_all_neo4j_graph()
    if createindices:
        create_neo4j_indices()
    if checkworkflow:
        check_graph_for_workflow_completeness(checkworkflow)
    if completeall:
        set_workflow_as_completed()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Notary Service Neo4j metrics')
    parser.add_argument('--generateids', metavar='INT', required=False,
                        help='Number of unique identifiers to generate')
    parser.add_argument('--importgraph', metavar='PATH', required=False,
                        help='Path to graphml file to be used as Neo4j import file')
    parser.add_argument('--checkworkflow', metavar='PATH', required=False,
                        help='Check all workflows for completeness')
    parser.add_argument('--completeall', action='store_true',
                        help='Set all workflow nodes to completed=True')
    parser.add_argument('--removegraph', action='store_true',
                        help='Remove all existing graphs from Neo4j')
    parser.add_argument('--createindices', action='store_true',
                        help='Create graph indices in Neo4j')
    args = parser.parse_args()

    # validate input
    if args.generateids is not None:
        try:
            args.generateids = int(args.generateids)
        except ValueError:
            print("Only integers are allowed for: --identifiers INT")
    if args.importgraph is not None:
        try:
            # check for files/uuid.txt
            graph_file = Path(args.importgraph)
            if not graph_file.is_file():
                raise FileNotFoundError("File does not exist or is not a file", graph_file)
            uuid_list = Path('files/uuid.json')
            if not uuid_list.is_file():
                raise FileNotFoundError("File not found", "files/uuid.json")
        except FileExistsError:
            print("Provided path does not return a file")
        if args.checkworkflow is not None:
            try:
                # check for files/uuid.txt
                graph_file = Path(args.checkworkflow)
                if not graph_file.is_file():
                    raise FileNotFoundError("File does not exist or is not a file", graph_file)
                uuid_list = Path('files/uuid.json')
                if not uuid_list.is_file():
                    raise FileNotFoundError("File not found", "files/uuid.json")
            except FileExistsError:
                print("Provided path does not return a file")
    print(args)

    main(
        generateids=args.generateids,
        importgraph=args.importgraph,
        removegraph=args.removegraph,
        checkworkflow=args.checkworkflow,
        completeall=args.completeall,
        createindices=args.createindices,
    )
