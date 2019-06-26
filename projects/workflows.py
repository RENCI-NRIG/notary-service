import os

from neo4j import GraphDatabase, basic_auth
from ns_workflow import Neo4jWorkflow

from datasets.models import Dataset, NSTemplate, MembershipNSTemplate
from users.models import Affiliation, NotaryServiceUser
from users.models import Role
from workflows.models import WorkflowNeo4j
from workflows.workflow_neo4j import create_workflow_from_template, delete_workflow_by_uuid
from .models import MembershipProjectWorkflow, Project, MembershipComanagePersonnel, \
    ProjectWorkflowUserCompletionByRole, MembershipInfrastructure, MembershipDatasets

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


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
    # create base workflow graphs for new datasets
    affiliation_list = Project.objects.values_list('affiliations__uuid', flat=True).filter(
        uuid=project_uuid
    )
    ds_list = Project.objects.values_list('datasets__uuid', flat=True).filter(
        uuid=project_uuid
    )
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
                        affiliation=Affiliation.objects.get(uuid=affiliation_uuid),
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
                        affiliation=Affiliation.objects.get(uuid=affiliation_uuid),
                        dataset=Dataset.objects.get(uuid=ds_uuid),
                        template=NSTemplate.objects.get(uuid=tplt_uuid),
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
                        is_generated=True,
                    )
    # delete workflow graphs for datasets removed from project
    # check by affiliation
    wf_affiliation_list = MembershipProjectWorkflow.objects.values_list('affiliation__uuid', flat=True).filter(
        project__uuid=project_uuid,
    ).distinct()
    project_affiliation_list = Project.objects.values_list('affiliations__uuid', flat=True).filter(
        uuid=project_uuid
    )
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
                        if not wf_obj.roles.filter(id=int(getattr(Role, 'PI_MEMBER'))).exists():
                            wf_obj.roles.add(int(getattr(Role, 'PI_MEMBER')))
                            print("Adding role " + str(Role.objects.get(id=int(getattr(Role, 'PI_MEMBER')))))
                    else:
                        if not wf_obj.roles.filter(id=int(getattr(Role, role))).exists():
                            wf_obj.roles.add(int(getattr(Role, role)))
                            print("Adding role " + str(Role.objects.get(id=int(getattr(Role, role)))))
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
    if user_obj.is_dp or user_obj.is_inp:
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
            affiliation=Affiliation.objects.get(
                uuid=user_obj.ns_affiliation
            ).id
        ).distinct()
    # get user roles
    user_roles = NotaryServiceUser.objects.values_list('roles__id', flat=True).filter(
        uuid=user_obj.uuid
    ).order_by('roles__id')
    # for each workflow, for each role, generate appropriate child nodes
    for workflow in project_workflows:
        workflow_roles = WorkflowNeo4j.objects.values_list('roles__id', flat=True).filter(
            uuid=workflow
        ).order_by('roles__id')
        print('Workflow: ' + str(workflow) + ' - ' + str(WorkflowNeo4j.objects.get(uuid=workflow).name))
        for role in user_roles:
            print('- Checking Role: ' + str(Role.objects.get(id=role)))
            if role in workflow_roles and validate_active_user_role_for_project(project_obj.id, user_obj.id, role, workflow):
                num_nodes = n.count_nodes(
                    graphId=str(workflow),
                    nodeRole=convert_comanage_role_id_to_neo4j_node_role(role_id=role),
                )
                print('  - Assign ' + str(num_nodes) + ' nodes to '
                      + user_obj.name + ' as ' + str(Role.objects.get(id=role)))
                is_complete = n.is_workflow_complete(
                    principalId=str(user_obj.uuid),
                    role=role,
                    graphId=str(workflow),
                )
                print('    is complete? ' + str(is_complete))
                # create project/person/workflow/role relationship if it does not exist
                if not ProjectWorkflowUserCompletionByRole.objects.filter(
                        project=project_obj,
                        person=user_obj,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=Role.objects.get(id=role),
                ).exists():
                    ProjectWorkflowUserCompletionByRole.objects.create(
                        project=project_obj,
                        person=user_obj,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=Role.objects.get(id=role),
                        is_complete=False
                    )
                else:
                    reln_obj = ProjectWorkflowUserCompletionByRole.objects.get(
                        project=project_obj,
                        person=user_obj,
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow),
                        role=Role.objects.get(id=role),
                    )
                    reln_obj.is_complete = is_complete
                    reln_obj.save()

    # update user workflow table for generation and completeness


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
    if role == 'STAFF':
        if MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                person=user_obj,
                comanage_staff_id__isnull=False,
        ):
            return True
    elif role == 'DP':
        if MembershipDatasets.objects.filter(
            project=project_obj,
            dataset__owner=user_obj
        ).exists():
            return True
    elif role == 'INP':
        if MembershipInfrastructure.objects.filter(
            project=project_obj,
            infrastructure__owner=user_obj
        ).exists():
            return True
    elif role == 'IG':
        if MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                person=user_obj,
                affiliation_ig__isnull=False,
        ):
            return True
    elif role == 'PI':
        if MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                person=user_obj,
                comanage_pi_members_id__isnull=False,
        ):
            return True

    return False


def take_user_through_workflow(user, workflow):
    role = convert_comanage_role_id_to_neo4j_node_role(user.role)
    assertions = []
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    is_complete = n.is_workflow_complete(
        principalId=str(user.uuid),
        role=role,
        graphId=workflow,
    )
    print('IS_COMPLETE: ' + str(role) + ' ' + str(is_complete))
    if is_complete:
        assertions.append("IS_COMPLETE")
        return assertions

    next_set = set()
    n.find_reachable_not_completed_nodes(
        principalId=str(user.uuid),
        role=role,
        graphId=workflow,
        nodeId="Start",
        incompleteNodeSet=next_set,
    )
    if len(next_set) == 0:
        assertions.append('Waiting on another user to complete their assertion(s) first...')
        return assertions
    for node in next_set:
        props = n.get_node_properties(graphId=workflow, nodeId=node)
        assertions.append(props)
    return assertions


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


def workflow_save_safe_token_and_complete(graph_id, node_id):
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
        token=assertion_scid
    )


def workflow_safe_assertion():
    return 'MOCK_ASSERTION_SCID'
