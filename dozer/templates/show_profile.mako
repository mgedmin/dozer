<%!
import sys
sys.setrecursionlimit(450)
%>
<h1>Viewing profile ID: ${id}</h1>

<h2>Environment</h2>
<div>${environ['SCRIPT_NAME'] + environ['PATH_INFO'] + environ['QUERY_STRING']|h}</div>

<h2>Profile</h2>
<div id="calltree">
    % for node in profile:
    ${show_node(node, 0)}
    % endfor
</div>

<%def name="show_node(node, depth)">
<div class="function-call" style="margin-left: ${10*depth}px;">
<span class="function">${node['function'] | h}</span> ran in 
<span class="time">${node['cost']}ms
</div>
% for called_node in node['calls']:
<%
    called = profile_data[called_node['function']]
    depth = depth + 1
    if depth > 30: continue
%>
${show_node(called, depth)}
% endfor
</%def>
<%inherit file="layout.mako"/>
