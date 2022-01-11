import os
import re
from datetime import datetime

from neo4j import GraphDatabase, basic_auth
from ns_workflow import Neo4jWorkflow

from datasets.models import Dataset, NSTemplate, MembershipNSTemplate
from users.models import Affiliation, NotaryServiceUser, WorkflowRole
from workflows.models import WorkflowNeo4j
from workflows.workflow_neo4j import create_workflow_from_template, delete_workflow_by_uuid
from .models import MembershipProjectWorkflow, Project, MembershipComanagePersonnel, \
    ProjectWorkflowUserCompletionByRole, MembershipInfrastructure, MembershipDatasets, ComanagePersonnel

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


def workflow_report_from_neo4j(workflow_uuid):
    """
    Harvest workflow information from Neo4j for completed tasks
    :param workflow_uuid:
    :return:
    """
    # print(str(workflow_uuid))
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + "' RETURN path"
    results = db.run(statement).graph()
    db.close()
    nodes = []
    for node in results.nodes:
        entry = {}
        entry['ts'] = str(node['ts'])
        if entry['ts'] != 'None':
            entry['ts'] = datetime.strptime(entry['ts'], "%Y-%m-%dT%H:%M:%S.%f%z")
            search = re.search(r"CN={1}(\w+\s*\w+\s*\w+)", str(node['principal']))
            if search is not None:
                entry['person'] = str(search.group(1))
            else:
                entry['person'] = ''
            entry['role'] = str(node['Role'])
            entry['tp'] = str(node['Type'])
            entry['label'] = str(node['label'])
            entry['sp'] = str(node['SAFEParameters'])
            pv = node['ParameterValue']
            if pv is None:
                entry['pv'] = str(None)
            elif len(pv[0]) == 1:
                entry['pv'] = str(pv)
            else:
                entry['pv'] = str(', '.join(list(pv)))
            nodes.append(entry)
    nodes = sorted(nodes, key=lambda i: i['ts'], reverse=True)
    return nodes


def create_base_project_workflows(project_uuid, user):
    """
    Create base project workflows from dataset associations
    for each dataset
      for each template
        new workflow object in django
        new graph: GraphID=uuid of django object
        insert table MembershipProjectWorkflow
          - ProjectID
          - GraphID
          - TemplateID
          - WorkflowNeo4jID
    """
    project = Project.objects.filter(uuid=project_uuid).first()
    affiliation_list = project.affiliation.values_list('uuid', flat=True)
    affiliation_list = list(set(affiliation_list))
    if affiliation_list[0] is None:
        return
    ds_list = Project.objects.values_list('datasets__uuid', flat=True).filter(
        uuid=project_uuid
    )
    if ds_list[0] is None:
        return
    for affiliation_uuid in affiliation_list:
        for ds_uuid in ds_list:
            tplt_list = NSTemplate.objects.values_list('uuid', 'graphml_definition').filter(
                uuid__in=MembershipNSTemplate.objects.values_list('template__uuid').filter(
                    dataset__uuid=ds_uuid
                )
            )
            # check for project, affiliation, dataset, template membership inclusion
            # if it does not exist, create a new base workflow
            for tplt_uuid, graphml_file in tplt_list:
                if not MembershipProjectWorkflow.objects.filter(
                        project__uuid=project_uuid,
                        affiliation__uuid=affiliation_uuid,
                        dataset__uuid=ds_uuid,
                        template__uuid=tplt_uuid,
                ).exists():
                    wf_name = str(Dataset.objects.get(uuid=ds_uuid).name) + ' (' \
                              + str(NSTemplate.objects.get(uuid=tplt_uuid).type) + ')'
                    nw_neo4j = WorkflowNeo4j.objects.create(
                        name=wf_name,
                        affiliation=Affiliation.objects.filter(uuid=affiliation_uuid).first(),
                        description=NSTemplate.objects.get(uuid=tplt_uuid).description,
                        dataset=Dataset.objects.get(uuid=ds_uuid),
                        template=NSTemplate.objects.get(uuid=tplt_uuid),
                        created_by=user,
                        modified_by=user,
                    )
                    # create workflow django object
                    workflow_uuid = nw_neo4j.uuid
                    if create_workflow_from_template(graphml_file, workflow_uuid):
                        nw_neo4j.loaded_in_neo4j = True
                        nw_neo4j.save()
                        set_neo4j_workflow_roles(workflow_uuid)
                    # create project / workflow relationship
                    MembershipProjectWorkflow.objects.create(
                        project=Project.objects.get(uuid=project_uuid),
                        affiliation=Affiliation.objects.filter(uuid=affiliation_uuid).first(),
                        dataset=Dataset.objects.get(uuid=ds_uuid),
                        template=NSTemplate.objects.get(uuid=tplt_uuid),
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
                        is_generated=True,
                    )
                    ns_project = Project.objects.filter(uuid=project_uuid).first()
                    ns_project.workflows.add(nw_neo4j)
                    ns_project.save()
    # delete workflow graphs for datasets removed from project
    # check by affiliation
    wf_affiliation_list = MembershipProjectWorkflow.objects.values_list('affiliation__uuid', flat=True).filter(
        project__uuid=project_uuid,
    ).distinct()
    project_affiliation_list = project.affiliation.values_list('uuid', flat=True)
    project_affiliation_list = list(set(affiliation_list))
    for wf_affiliation_uuid in wf_affiliation_list:
        if wf_affiliation_uuid not in project_affiliation_list:
            wf_remove_list = MembershipProjectWorkflow.objects.values_list('workflow__uuid', flat=True).filter(
                project__uuid=project_uuid,
                affiliation__uuid=wf_affiliation_uuid,
            )
            for wf_remove_uuid in wf_remove_list:
                # remove workflow
                delete_workflow_by_uuid(wf_remove_uuid)
                # remove django object
                WorkflowNeo4j.objects.filter(uuid=wf_remove_uuid).delete()
                # remove relationship
                MembershipProjectWorkflow.objects.filter(workflow__uuid=wf_remove_uuid).delete()
    # check by dataset
    wf_ds_list = MembershipProjectWorkflow.objects.values_list('dataset__uuid', flat=True).filter(
        project__uuid=project_uuid,
    )
    for wf_ds_uuid in wf_ds_list:
        if wf_ds_uuid not in ds_list:
            wf_list = MembershipProjectWorkflow.objects.values_list('workflow__uuid', flat=True).filter(
                project__uuid=project_uuid,
                dataset__uuid=wf_ds_uuid,
            )
            for wf_uuid in wf_list:
                # delete the workflow in neo4j
                delete_workflow_by_uuid(wf_uuid)
                # delete wth workflow django object
                WorkflowNeo4j.objects.filter(
                    uuid=wf_uuid
                ).delete()
                # delete the project / workflow relationship
                MembershipProjectWorkflow.objects.filter(
                    project__uuid=project_uuid,
                    dataset__uuid=wf_ds_uuid,
                    workflow__uuid=wf_uuid
                ).delete()


def set_neo4j_workflow_roles(workflow_uuid):
    wf_obj = WorkflowNeo4j.objects.get(uuid=workflow_uuid)
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + \
                "' AND n.SAFEType in ['common-set', 'template-user-set', 'None'] RETURN path"
    results = db.run(statement).graph()
    db.close()
    for node in results.nodes:
        for key in node.keys():
            if key == 'Role':
                roles = str(node[key])
                for role in roles.split(','):
                    if role == 'None':
                        pass
                    elif role == 'PI':
                        # if not wf_obj.roles.filter(id=int(getattr(Role, 'PI_ADMIN'))).exists():
                        #     wf_obj.roles.add(int(getattr(Role, 'PI_ADMIN')))
                        if not wf_obj.roles.filter(id=int(getattr(WorkflowRole, 'PI_MEMBER'))).exists():
                            wf_obj.roles.add(int(getattr(WorkflowRole, 'PI_MEMBER')))
                            # print("Adding role " + str(WorkflowRole.objects.get(id=int(getattr(WorkflowRole, 'PI_MEMBER')))))
                    else:
                        if not wf_obj.roles.filter(id=int(getattr(WorkflowRole, role))).exists():
                            wf_obj.roles.add(int(getattr(WorkflowRole, role)))
                            # print("Adding role " + str(WorkflowRole.objects.get(id=int(getattr(WorkflowRole, role)))))
    wf_obj.save()


def generate_neo4j_user_workflow_status(project_obj, user_obj):
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    # get workflows from project and match to user by affiliation
    if user_obj.is_dp() or user_obj.is_inp():
        # if user is DP or INP, show all workflows that relate to them (regardless of affiliation)
        project_workflows = WorkflowNeo4j.objects.values_list('uuid', flat=True).filter(
            uuid__in=MembershipProjectWorkflow.objects.values_list('workflow__uuid').filter(
                project=project_obj
            )
        ).distinct()
    else:
        project_workflows = WorkflowNeo4j.objects.values_list('uuid', flat=True).filter(
            uuid__in=MembershipProjectWorkflow.objects.values_list('workflow__uuid').filter(
                project=project_obj
            ),
            affiliation=Affiliation.objects.filter(
                uuid=user_obj.affiliation.uuid
            ).first().id
        ).distinct()
    # get user roles
    # user_roles = NotaryServiceUser.objects.values_list('roles__id', flat=True).filter(
    #     uuid=user_obj.uuid
    # ).order_by('roles__id')
    # user_roles = [user_obj.role]
    # user_roles = []
    user_roles = get_converted_user_roles_per_project_as_id(project_obj, user_obj)
    # print(user_roles)
    # for each workflow, for each role, generate appropriate child nodes
    for workflow in project_workflows:
        workflow_roles = WorkflowNeo4j.objects.values_list('roles__id', flat=True).filter(
            uuid=workflow
        ).order_by('roles__id')
        # print('Workflow: ' + str(workflow) + ' - ' + str(WorkflowNeo4j.objects.get(uuid=workflow).name))
        for role in user_roles:
            # print('- Checking Role: ' + str(WorkflowRole.objects.get(id=role)))
            if role in workflow_roles and validate_active_user_role_for_project(project_obj.id, user_obj.id, role,
                                                                                workflow):
                # num_nodes = n.count_nodes(
                #     graphId=str(workflow),
                #     nodeRole=convert_comanage_role_id_to_neo4j_node_role(role_id=role),
                # )
                # print('  - Assign ' + str(num_nodes) + ' nodes to '
                #       + user_obj.name + ' as ' + str(Role.objects.get(id=role)))
                is_complete = n.is_workflow_complete(
                    principalId=str(user_obj.cert_subject_dn),
                    role=role,
                    graphId=str(workflow),
                )
                # print('  is complete? ' + str(is_complete))
                # create project/person/workflow/role relationship if it does not exist
                if not ProjectWorkflowUserCompletionByRole.objects.filter(
                        project=project_obj,
                        person=user_obj,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=WorkflowRole.objects.get(id=role),
                ).exists():
                    ProjectWorkflowUserCompletionByRole.objects.create(
                        project=project_obj,
                        person=user_obj,
                        dataset=WorkflowNeo4j.objects.get(uuid=workflow).dataset,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=WorkflowRole.objects.get(id=role),
                        is_complete=False
                    )
                else:
                    reln_obj = ProjectWorkflowUserCompletionByRole.objects.get(
                        project=project_obj,
                        person=user_obj,
                        dataset=WorkflowNeo4j.objects.get(uuid=workflow).dataset,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=WorkflowRole.objects.get(id=role),
                    )
                    reln_obj.is_complete = is_complete
                    reln_obj.save()


def convert_comanage_role_id_to_neo4j_node_role(role_id):
    """
    converts role_id to string based on Role model (from users)
    :param role_id:
    :return:
    """
    index = int(role_id) - 1
    ROLE_CHOICES = [
        'NSADMIN',
        'STAFF',
        'DP',
        'INP',
        'IG',
        'PI',
        'PI',
        'NO_ROLE'
    ]
    return str(ROLE_CHOICES[index])


def validate_active_user_role_for_project(project_obj, user_obj, role_id, workflow_uuid):
    """
    checks for nodes to assign to user based on their role within the project
    :param project_obj:
    :param user_obj:
    :param role_id:
    :return:
    """
    role = convert_comanage_role_id_to_neo4j_node_role(role_id)
    user = NotaryServiceUser.objects.filter(id=user_obj).first()
    ns_person_roles = [r.co_cou.name for r in user.roles.all()]
    ns_project = Project.objects.filter(id=project_obj).first()
    if role == 'STAFF':
        if str(ns_project.uuid) + os.getenv('COU_FLAG_STAFF') in ns_person_roles:
            return True
    elif role == 'DP':
        datasets = ns_project.datasets.all()
        dataset_owners = [d.owner for d in datasets]
        if user in dataset_owners:
            return True
    elif role == 'INP':
        if ns_project.infrastructure:
            if user == ns_project.infrastructure.owner:
                return True
    elif role == 'IG':
        igs = ns_project.project_igs.all()
        if user in igs:
            return True
    elif role == 'PI':
        if str(ns_project.uuid) + os.getenv('COU_FLAG_PI_MEMBER') in ns_person_roles:
            return True

    return False


def get_next_set_by_role(user_obj, workflow, role: str = None):
    if not role:
        role = convert_comanage_role_id_to_neo4j_node_role(user_obj.role)
    else:
        role = role
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    next_set = set()
    n.find_reachable_not_completed_nodes(
        principalId=str(user_obj.cert_subject_dn),
        role=role,
        graphId=workflow,
        nodeId="Start",
        incompleteNodeSet=next_set,
    )
    return next_set


def take_user_through_workflow(user_obj, workflow):
    ns_project = Project.objects.filter(workflows__uuid__in=[workflow]).first()
    user_roles = get_converted_user_roles_per_project_as_name(project=ns_project, user=user_obj)
    assertions = []
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    next_set = set()
    # print(user_roles)
    for role in user_roles:
        n.find_reachable_not_completed_nodes(
            principalId=str(user_obj.cert_subject_dn),
            role=role,
            graphId=workflow,
            nodeId="Start",
            incompleteNodeSet=next_set,
        )
        # print(next_set)
        if len(next_set) == 0:
            is_complete = n.is_workflow_complete(
                principalId=str(user_obj.cert_subject_dn),
                role=role,
                graphId=workflow,
            )
            if is_complete:
                assertions.append({'Role': role, 'ID': 'IS_COMPLETE', 'id': role + '0'})
            else:
                assertions.append({'Role': role, 'ID': 'Assertions by other roles required before proceeding...', 'id': role + '1'})
        else:
            for node in next_set:
                props = n.get_node_properties(graphId=workflow, nodeId=node)
                assertions.append(props)
    assertions = list({v['id']:v for v in assertions}.values())
    return assertions


def workflow_make_conditional_selection_and_disable_branches(graph_id, node_id, cond_value):
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir
    )
    n.make_conditional_selection_and_disable_branches(
        graphId=graph_id,
        nodeId=node_id,
        value=cond_value
    )


def workflow_update_node_property(graph_id, node_id, prop_name, prop_value):
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir
    )
    n.update_node_property(
        graphId=graph_id,
        nodeId=node_id,
        propName=prop_name,
        propVal=prop_value
    )


def workflow_save_safe_token_and_complete(graph_id, node_id, user_dn):
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir
    )
    assertion_scid = workflow_safe_assertion()
    n.save_safe_token_and_complete(
        graphId=graph_id,
        nodeId=node_id,
        token=assertion_scid,
        principalId=user_dn
    )


def get_converted_user_roles_per_project_as_id(project: Project, user: NotaryServiceUser) -> list:
    """
    Reference for WorkflowRole
        - NSADMIN   = 1  # CO:COU:NOTARY_SERVICE-NSADMIN:admins
        - STAFF     = 2  # CO:COU:PROJECT_NAME-STAFF:members:active
        - DP        = 3  # CO:COU:PROJECT_NAME-DP:members:active
        - INP       = 4  # CO:COU:PROJECT_NAME-INP:members:active
        - IG        = 5  # CO:COU:PROJECT_NAME-IG:members:active
        - PI_ADMIN  = 6  # CO:COU:PROJECT_NAME-PI:admins
        - PI_MEMBER = 7  # CO:COU:PROJECT_NAME-PI:members:active
        - NO_ROLE   = 8  # No role found in COmanage
    """
    user_roles = []
    roles = user.roles.all()
    for role in roles:
        # project membership STAFF or PI
        if role.co_cou.name == str(project.uuid) + os.getenv('COU_FLAG_STAFF'):
            user_roles.append(2)
        elif role.co_cou.name == str(project.uuid) + os.getenv('COU_FLAG_PI_MEMBER'):
            user_roles.append(7)
        # data provider DP
        elif role.co_cou.name == os.getenv('ROLE_DP'):
            datasets = project.datasets.all()
            dps = [d.owner for d in datasets]
            if user in dps:
                user_roles.append(3)
        # infrastructure provider INP
        elif role.co_cou.name == os.getenv('ROLE_INP'):
            if project.infrastructure:
                if user == project.infrastructure.owner:
                    user_roles.append(4)
        # institutional governance IG
        elif role.co_cou.name == os.getenv('ROLE_IG'):
            if user in project.project_igs.all():
                user_roles.append(5)


    return user_roles


def get_converted_user_roles_per_project_as_name(project: Project, user: NotaryServiceUser) -> list:
    """
    Reference for WorkflowRole
        - NSADMIN   = 1  # CO:COU:NOTARY_SERVICE-NSADMIN:admins
        - STAFF     = 2  # CO:COU:PROJECT_NAME-STAFF:members:active
        - DP        = 3  # CO:COU:PROJECT_NAME-DP:members:active
        - INP       = 4  # CO:COU:PROJECT_NAME-INP:members:active
        - IG        = 5  # CO:COU:PROJECT_NAME-IG:members:active
        - PI_ADMIN  = 6  # CO:COU:PROJECT_NAME-PI:admins
        - PI_MEMBER = 7  # CO:COU:PROJECT_NAME-PI:members:active
        - NO_ROLE   = 8  # No role found in COmanage
    """
    user_roles = []
    roles = user.roles.all()
    for role in roles:
        # project membership STAFF or PI
        if role.co_cou.name == str(project.uuid) + os.getenv('COU_FLAG_STAFF'):
            user_roles.append('STAFF')
        elif role.co_cou.name == str(project.uuid) + os.getenv('COU_FLAG_PI_MEMBER'):
            user_roles.append('PI')
        # data provider DP
        elif role.co_cou.name == os.getenv('ROLE_DP'):
            datasets = project.datasets.all()
            dps = [d.owner for d in datasets]
            if user in dps:
                user_roles.append('DP')
        # infrastructure provider INP
        elif role.co_cou.name == os.getenv('ROLE_INP'):
            if project.infrastructure:
                if user == project.infrastructure.owner:
                    user_roles.append('INP')
        # institutional governance IG
        elif role.co_cou.name == os.getenv('ROLE_IG'):
            if user in project.project_igs.all():
                user_roles.append('IG')

    return user_roles


def workflow_safe_assertion():
    return 'MOCK_ASSERTION_SCID'
