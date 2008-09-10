<%!
import sys
sys.setrecursionlimit(450)
%>
<div id="profiler">
    <h1>Viewing profile ID: ${id}</h1>

    <h2>Environment</h2>
    <div>${environ['SCRIPT_NAME'] + environ['PATH_INFO'] + environ['QUERY_STRING']|h}</div>

    <h2>Profile</h2>
    <div id="profile">\
        <ul>
        % for node in profile:
        ${show_node(node, 0, node['cost'])}\
        % endfor
        </ul>
    </div>
</div>

<%def name="show_node(node, depth, tottime)">
<% 
    import random
    parent_id = ''.join([str(random.randrange(0,10)) for x in range(0,9)])
    child_nodes = [x for x in node['calls'] if not x['builtin']]
    has_children = len(child_nodes) > 0
    if int(float(tottime)) == 0:
        proj_width = 1
    else:
        factor = float(400) / float(tottime)
        proj_width = int(float(factor) * float(node['cost']))
%>
% if has_children:
<li id="step_${parent_id}" class="step with-children">\
% else:
<li id="step_${parent_id}" class="step">\
% endif
<ul class="step-info">
<li class="title"><p><span class="time">${node['cost']}ms</span>
% if has_children:
<a href="#" onclick="$('#children_step_${parent_id}').toggle();$('#step_${parent_id}').toggleClassName('opened');return false;">\
${node['function']|h}</a>\
% else:
${node['function']|h}\
% endif
</p></li>
<li class="bar">
    <ul class="profile_bar">
        <li class="layer" style="width: ${proj_width}px;">&nbsp;</li>
    </ul>
    <br style="clear: left;" />
</li>
<li style="clear: left;">&nbsp;</li>
</ul>\
% if has_children:
<ul id="children_step_${parent_id}" class="profile_children" style="display:none;">\
% for called_node in node['calls']:
<%
    called = profile_data[called_node['function']]
    if called_node['builtin']: continue
    depth = depth + 1
    if depth > 30: continue
%>
${show_node(called, depth, tottime)}\
% endfor
<li style="clear: left;">&nbsp;</li>
</ul>
</li>
% endif
</%def>
<%inherit file="layout.mako"/>
<%def name="javascript()">
${parent.javascript()}
<script>
$('div.function-call:lt(2)').show();
</script>
</%def>