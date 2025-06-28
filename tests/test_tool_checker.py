from core import tool_checker

def test_check_tools_all_present(monkeypatch):
    selected_tasks = ['Automated Subdomain Enumeration']
    tasks_config = {
        'Automated Subdomain Enumeration': [
            'subfinder -d {target} -o {output}/subdomains/subfinder.txt',
            'amass enum -passive -d {target} -o {output}/subdomains/amass.txt'
        ]
    }
    tools_config = {
        'subfinder': {'check': 'subfinder', 'install': 'install subfinder'},
        'amass': {'check': 'amass', 'install': 'install amass'}
    }
    monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/' + x)
    missing = tool_checker.check_tools(selected_tasks, tasks_config, tools_config)
    assert missing == {}

def test_check_tools_missing(monkeypatch):
    selected_tasks = ['Automated Subdomain Enumeration']
    tasks_config = {
        'Automated Subdomain Enumeration': [
            'subfinder -d {target} -o {output}/subdomains/subfinder.txt',
            'amass enum -passive -d {target} -o {output}/subdomains/amass.txt'
        ]
    }
    tools_config = {
        'subfinder': {'check': 'subfinder', 'install': 'install subfinder'},
        'amass': {'check': 'amass', 'install': 'install amass'}
    }
    monkeypatch.setattr('shutil.which', lambda x: None if x == 'amass' else '/usr/bin/' + x)
    missing = tool_checker.check_tools(selected_tasks, tasks_config, tools_config)
    assert 'amass' in missing
