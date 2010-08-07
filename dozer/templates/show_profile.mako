<%!
import sys
sys.setrecursionlimit(450)
%>
<div id="profiler">
    <h1>Viewing profile ID: ${id}</h1>

    <h2>URL</h2>

    <div>${environ['SCRIPT_NAME'] + environ['PATH_INFO'] + environ['QUERY_STRING']|h}</div>

    <h2 onclick="$('#environment').toggle()" style="cursor: pointer">Environment</h2>

    <dl id="environment" style="display: none">
      <table id="environment">
        % for key, value in sorted(environ.items()):
        <tr>
            <th>${key|h}</th>
            <td>${value|h}</td>
        </tr>
        % endfor
      </table>
    </dl>

    <h2>Profile</h2>
    <div id="profile">\
        <ul>
        % for node in profile:
        <%
            if "disable' of '_lsprof.Profiler" in node['function']:
                continue
            if '<module>' in node['function'] and '<string>:1' in node['function']:
                node = profile_data[node['calls'][0]['function']]
        %>
        ${show_node(node, 0, node['cost'])}\
        % endfor
        </ul>
    </div>
</div>

<%def name="show_node(node, depth, tottime, callcount=1)">
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
% if callcount > 1:
<span class="callcount">&#x2715;${callcount}</span>
% endif
% if has_children:
<a href="#" title="${node['filename']}:${node['line_no']}" onclick="$('#children_step_${parent_id}').toggle();$('#step_${parent_id}').toggleClass('opened');return false;">\
${node['func_name']|h}</a>\
% else:
<span title="${node['filename']}:${node['line_no']}">${node['func_name']|h}</span>\
% endif
</p></li>
<li class="bar">
    <ul class="profile_bar">
        <li class="layer" style="width: ${proj_width}px;">&nbsp;</li>
    </ul>
    <br style="clear: left;" />
</li>
<li style="clear: left;"> </li>
</ul>\
% if has_children:
<% depth = depth + 1 %>
<ul id="children_step_${parent_id}" class="profile_children"\
% if proj_width < 200:
 style="display:none;"\
% endif
>\
% for called_node in sorted(node['calls'], key=lambda n: float(n['cost']), reverse=True):
<%
    called = profile_data[called_node['function']]
    if called_node['builtin']: continue
    if depth > 20: continue
%>
${show_node(called, depth, tottime, called_node['callcount'])}\
% endfor
<li style="clear: left;"> </li>
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
