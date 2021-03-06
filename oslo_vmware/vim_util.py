# Copyright (c) 2014 VMware, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
The VMware API utility module.
"""

from suds import sudsobject

from oslo.utils import timeutils


def get_moref(value, type_):
    """Get managed object reference.

    :param value: value of the managed object
    :param type_: type of the managed object
    :returns: managed object reference with given value and type
    """
    moref = sudsobject.Property(value)
    moref._type = type_
    return moref


def build_selection_spec(client_factory, name):
    """Builds the selection spec.

    :param client_factory: factory to get API input specs
    :param name: name for the selection spec
    :returns: selection spec
    """
    sel_spec = client_factory.create('ns0:SelectionSpec')
    sel_spec.name = name
    return sel_spec


def build_traversal_spec(client_factory, name, type_, path, skip, select_set):
    """Builds the traversal spec.

    :param client_factory: factory to get API input specs
    :param name: name for the traversal spec
    :param type_: type of the managed object
    :param path: property path of the managed object
    :param skip: whether or not to filter the object identified by param path
    :param select_set: set of selection specs specifying additional objects
                       to filter
    :returns: traversal spec
    """
    traversal_spec = client_factory.create('ns0:TraversalSpec')
    traversal_spec.name = name
    traversal_spec.type = type_
    traversal_spec.path = path
    traversal_spec.skip = skip
    traversal_spec.selectSet = select_set
    return traversal_spec


def build_recursive_traversal_spec(client_factory):
    """Builds recursive traversal spec to traverse managed object hierarchy.

    :param client_factory: factory to get API input specs
    :returns: recursive traversal spec
    """
    visit_folders_select_spec = build_selection_spec(client_factory,
                                                     'visitFolders')
    # Next hop from Datacenter
    dc_to_hf = build_traversal_spec(client_factory,
                                    'dc_to_hf',
                                    'Datacenter',
                                    'hostFolder',
                                    False,
                                    [visit_folders_select_spec])
    dc_to_vmf = build_traversal_spec(client_factory,
                                     'dc_to_vmf',
                                     'Datacenter',
                                     'vmFolder',
                                     False,
                                     [visit_folders_select_spec])
    dc_to_netf = build_traversal_spec(client_factory,
                                      'dc_to_netf',
                                      'Datacenter',
                                      'networkFolder',
                                      False,
                                      [visit_folders_select_spec])

    # Next hop from HostSystem
    h_to_vm = build_traversal_spec(client_factory,
                                   'h_to_vm',
                                   'HostSystem',
                                   'vm',
                                   False,
                                   [visit_folders_select_spec])

    # Next hop from ComputeResource
    cr_to_h = build_traversal_spec(client_factory,
                                   'cr_to_h',
                                   'ComputeResource',
                                   'host',
                                   False,
                                   [])
    cr_to_ds = build_traversal_spec(client_factory,
                                    'cr_to_ds',
                                    'ComputeResource',
                                    'datastore',
                                    False,
                                    [])

    rp_to_rp_select_spec = build_selection_spec(client_factory, 'rp_to_rp')
    rp_to_vm_select_spec = build_selection_spec(client_factory, 'rp_to_vm')

    cr_to_rp = build_traversal_spec(client_factory,
                                    'cr_to_rp',
                                    'ComputeResource',
                                    'resourcePool',
                                    False,
                                    [rp_to_rp_select_spec,
                                     rp_to_vm_select_spec])

    # Next hop from ClusterComputeResource
    ccr_to_h = build_traversal_spec(client_factory,
                                    'ccr_to_h',
                                    'ClusterComputeResource',
                                    'host',
                                    False,
                                    [])
    ccr_to_ds = build_traversal_spec(client_factory,
                                     'ccr_to_ds',
                                     'ClusterComputeResource',
                                     'datastore',
                                     False,
                                     [])
    ccr_to_rp = build_traversal_spec(client_factory,
                                     'ccr_to_rp',
                                     'ClusterComputeResource',
                                     'resourcePool',
                                     False,
                                     [rp_to_rp_select_spec,
                                      rp_to_vm_select_spec])
    # Next hop from ResourcePool
    rp_to_rp = build_traversal_spec(client_factory,
                                    'rp_to_rp',
                                    'ResourcePool',
                                    'resourcePool',
                                    False,
                                    [rp_to_rp_select_spec,
                                     rp_to_vm_select_spec])
    rp_to_vm = build_traversal_spec(client_factory,
                                    'rp_to_vm',
                                    'ResourcePool',
                                    'vm',
                                    False,
                                    [rp_to_rp_select_spec,
                                     rp_to_vm_select_spec])

    # Get the assorted traversal spec which takes care of the objects to
    # be searched for from the rootFolder
    traversal_spec = build_traversal_spec(client_factory,
                                          'visitFolders',
                                          'Folder',
                                          'childEntity',
                                          False,
                                          [visit_folders_select_spec,
                                           h_to_vm,
                                           dc_to_hf,
                                           dc_to_vmf,
                                           dc_to_netf,
                                           cr_to_ds,
                                           cr_to_h,
                                           cr_to_rp,
                                           ccr_to_h,
                                           ccr_to_ds,
                                           ccr_to_rp,
                                           rp_to_rp,
                                           rp_to_vm])
    return traversal_spec


def build_property_spec(client_factory, type_='VirtualMachine',
                        properties_to_collect=None, all_properties=False):
    """Builds the property spec.

    :param client_factory: factory to get API input specs
    :param type_: type of the managed object
    :param properties_to_collect: names of the managed object properties to be
                                  collected while traversal filtering
    :param all_properties: whether all properties of the managed object need
                           to be collected
    :returns: property spec
    """
    if not properties_to_collect:
        properties_to_collect = ['name']

    property_spec = client_factory.create('ns0:PropertySpec')
    property_spec.all = all_properties
    property_spec.pathSet = properties_to_collect
    property_spec.type = type_
    return property_spec


def build_object_spec(client_factory, root_folder, traversal_specs):
    """Builds the object spec.

    :param client_factory: factory to get API input specs
    :param root_folder: root folder reference; the starting point of traversal
    :param traversal_specs: filter specs required for traversal
    :returns: object spec
    """
    object_spec = client_factory.create('ns0:ObjectSpec')
    object_spec.obj = root_folder
    object_spec.skip = False
    object_spec.selectSet = traversal_specs
    return object_spec


def build_property_filter_spec(client_factory, property_specs, object_specs):
    """Builds the property filter spec.

    :param client_factory: factory to get API input specs
    :param property_specs: property specs to be collected for filtered objects
    :param object_specs: object specs to identify objects to be filtered
    :returns: property filter spec
    """
    property_filter_spec = client_factory.create('ns0:PropertyFilterSpec')
    property_filter_spec.propSet = property_specs
    property_filter_spec.objectSet = object_specs
    return property_filter_spec


def get_objects(vim, type_, max_objects, properties_to_collect=None,
                all_properties=False):
    """Get all managed object references of the given type.

    It is the caller's responsibility to continue or cancel retrieval.

    :param vim: Vim object
    :param type_: type of the managed object
    :param max_objects: maximum number of objects that should be returned in
                        a single call
    :param properties_to_collect: names of the managed object properties to be
                                  collected
    :param all_properties: whether all properties of the managed object need to
                           be collected
    :returns: all managed object references of the given type
    :raises: VimException, VimFaultException, VimAttributeException,
             VimSessionOverLoadException, VimConnectionException
    """
    if not properties_to_collect:
        properties_to_collect = ['name']

    client_factory = vim.client.factory
    recur_trav_spec = build_recursive_traversal_spec(client_factory)
    object_spec = build_object_spec(client_factory,
                                    vim.service_content.rootFolder,
                                    [recur_trav_spec])
    property_spec = build_property_spec(
        client_factory,
        type_=type_,
        properties_to_collect=properties_to_collect,
        all_properties=all_properties)
    property_filter_spec = build_property_filter_spec(client_factory,
                                                      [property_spec],
                                                      [object_spec])
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = max_objects
    return vim.RetrievePropertiesEx(vim.service_content.propertyCollector,
                                    specSet=[property_filter_spec],
                                    options=options)


def get_object_properties(vim, moref, properties_to_collect):
    """Get properties of the given managed object.

    :param vim: Vim object
    :param moref: managed object reference
    :param properties_to_collect: names of the managed object properties to be
                                  collected
    :returns: properties of the given managed object
    :raises: VimException, VimFaultException, VimAttributeException,
             VimSessionOverLoadException, VimConnectionException
    """
    if moref is None:
        return None

    client_factory = vim.client.factory
    all_properties = (properties_to_collect is None or
                      len(properties_to_collect) == 0)
    property_spec = build_property_spec(
        client_factory,
        type_=moref._type,
        properties_to_collect=properties_to_collect,
        all_properties=all_properties)
    object_spec = build_object_spec(client_factory, moref, [])
    property_filter_spec = build_property_filter_spec(client_factory,
                                                      [property_spec],
                                                      [object_spec])

    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = 1
    retrieve_result = vim.RetrievePropertiesEx(
        vim.service_content.propertyCollector,
        specSet=[property_filter_spec],
        options=options)
    cancel_retrieval(vim, retrieve_result)
    return retrieve_result.objects


def _get_token(retrieve_result):
    """Get token from result to obtain next set of results.

    :retrieve_result: Result of RetrievePropertiesEx API call
    :returns: token to obtain next set of results; None if no more results.
    """
    return getattr(retrieve_result, 'token', None)


def cancel_retrieval(vim, retrieve_result):
    """Cancels the retrieve operation if necessary.

    :param vim: Vim object
    :param retrieve_result: result of RetrievePropertiesEx API call
    :raises: VimException, VimFaultException, VimAttributeException,
             VimSessionOverLoadException, VimConnectionException
    """
    token = _get_token(retrieve_result)
    if token:
        collector = vim.service_content.propertyCollector
        vim.CancelRetrievePropertiesEx(collector, token=token)


def continue_retrieval(vim, retrieve_result):
    """Continue retrieving results, if available.

    :param vim: Vim object
    :param retrieve_result: result of RetrievePropertiesEx API call
    :raises: VimException, VimFaultException, VimAttributeException,
             VimSessionOverLoadException, VimConnectionException
    """
    token = _get_token(retrieve_result)
    if token:
        collector = vim.service_content.propertyCollector
        return vim.ContinueRetrievePropertiesEx(collector, token=token)


def get_object_property(vim, moref, property_name):
    """Get property of the given managed object.

    :param vim: Vim object
    :param moref: managed object reference
    :param property_name: name of the property to be retrieved
    :returns: property of the given managed object
    :raises: VimException, VimFaultException, VimAttributeException,
             VimSessionOverLoadException, VimConnectionException
    """
    props = get_object_properties(vim, moref, [property_name])
    prop_val = None
    if props:
        prop = None
        if hasattr(props[0], 'propSet'):
            # propSet will be set only if the server provides value
            # for the field
            prop = props[0].propSet
        if prop:
            prop_val = prop[0].val
    return prop_val


def find_extension(vim, key):
    """Looks for an existing extension.

    :param vim: Vim object
    :param key: the key to search for
    :returns: the data object Extension or None
    """
    extension_manager = vim.service_content.extensionManager
    return vim.client.service.FindExtension(extension_manager, key)


def register_extension(vim, key, type, label='OpenStack',
                       summary='OpenStack services', version='1.0'):
    """Create a new extention.

    :param vim: Vim object
    :param key: the key for the extension
    :param type: Managed entity type, as defined by the extension. This
                 matches the type field in the configuration about a
                 virtual machine or vApp
    :param label: Display label
    :param summary: Summary description
    :param version: Extension version number as a dot-separated string
    """
    extension_manager = vim.service_content.extensionManager
    client_factory = vim.client.factory
    os_ext = client_factory.create('ns0:Extension')
    os_ext.key = key
    entity_info = client_factory.create('ns0:ExtManagedEntityInfo')
    entity_info.type = type
    os_ext.managedEntityInfo = [entity_info]
    os_ext.version = version
    desc = client_factory.create('ns0:Description')
    desc.label = label
    desc.summary = summary
    os_ext.description = desc
    os_ext.lastHeartbeatTime = timeutils.strtime()
    vim.client.service.RegisterExtension(extension_manager, os_ext)


def get_vc_version(session):
    """Return the dot-separated vCenter version string. For example, "1.2".

    :param session: vCenter soap session
    :return: vCenter version
    """
    return session.vim.service_content.about.version


def get_inventory_path(vim, entity_ref, max_objects=100):
    """Get the inventory path of a managed entity.

    :param vim: Vim object
    :param entity_ref: managed entity reference
    :param max_objects: maximum number of objects that should be returned in
                        a single call
    :return: inventory path of the entity_ref
    """
    client_factory = vim.client.factory
    property_collector = vim.service_content.propertyCollector

    prop_spec = build_property_spec(client_factory, 'ManagedEntity',
                                    ['name', 'parent'])
    select_set = build_selection_spec(client_factory, 'ParentTraversalSpec')
    select_set = build_traversal_spec(
        client_factory, 'ParentTraversalSpec', 'ManagedEntity', 'parent',
        False, [select_set])
    obj_spec = build_object_spec(client_factory, entity_ref, select_set)
    prop_filter_spec = build_property_filter_spec(client_factory,
                                                  [prop_spec], [obj_spec])
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = max_objects
    retrieve_result = vim.RetrievePropertiesEx(
        property_collector,
        specSet=[prop_filter_spec],
        options=options)
    entity_name = None
    propSet = None
    path = ""
    while retrieve_result:
        for obj in retrieve_result.objects:
            if hasattr(obj, 'propSet'):
                propSet = obj.propSet
                if len(propSet) >= 1 and not entity_name:
                    entity_name = propSet[0].val
                elif len(propSet) >= 1:
                    path = '%s/%s' % (propSet[0].val, path)
        retrieve_result = continue_retrieval(vim, retrieve_result)
    # NOTE(arnaud): slice to exclude the root folder from the result.
    if propSet is not None and len(propSet) > 0:
        path = path[len(propSet[0].val):]
    if entity_name is None:
        entity_name = ""
    return '%s%s' % (path, entity_name)


def get_http_service_request_spec(client_factory, method, uri):
    """Build a HTTP service request spec.

    :param client_factory: factory to get API input specs
    :param method: HTTP method (GET, POST, PUT)
    :param uri: target URL
    """
    http_service_request_spec = client_factory.create(
        'ns0:SessionManagerHttpServiceRequestSpec')
    http_service_request_spec.method = method
    http_service_request_spec.url = uri
    return http_service_request_spec
