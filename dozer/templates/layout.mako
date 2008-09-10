<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>${self.title()}</title>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    ${self.styles()}
</head>
<body>
    ${next.body()}
    ${self.javascript()}
</body>
</html>
<%def name="title()">Dozer - Profiler</%def>
##
<%def name="styles()">
</%def>
<%def name="javascript()">
</%def>