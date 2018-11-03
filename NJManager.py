import json
import pprint
from operator import attrgetter

class NJFileManager:
    def list_drives(self):
        pass

    def list_directories(self, path):
        pass

    def list_files(self, path):
        pass

    def get_file_thumbnail(self, path, size):
        pass

    def copy_files(self, destination, files):
        pass

    def move_files(self, destination, files):
        pass

    def create_directory(self, directory):
        pass

    def create_file(self, path):
        pass

    def download_file(self, path, identifier, size):
        pass

    def upload_file(self, path, identifier):
        pass

    def create_rar(self, rar_name, working_directory, arguments):
        pass

    def download_from_url(self, url, path):
        pass

    def execute_files(self, paths):
        pass

    def delete_files(self, paths):
        pass

    def get_files(self, paths):
        pass

    def write_file(self, path, contents):
        pass

    def rename_file(self, path, name):
        pass

    def rename_directory(self, path, name):
        pass


class NJServiceManager:

    def __init__(self, load=None):
        self._services = []
        if load is not None:
            self.load_services(load)

    class Service:
        def __init__(self, service_name, display_name, service_type, status, stoppable):
            self.name = service_name
            self.display_name = display_name
            self.service_type = service_type
            self.status = status
            self.stoppable = stoppable

        def stop(self):
            self.status = "Stopped"

        def start(self):
            self.status = "Running"

        def pause(self):
            pass

    def load_services(self, path):
        service_list = json.load(open(path))
        for service in service_list:
            service_name = service.get("service_name")
            display_name = service.get("display_name")
            service_type = service.get("service_type")
            status = service.get("status")
            stoppable = service.get("stoppable")
            self._services.append(
                    self.Service(service_name, display_name,
                        service_type, status, stoppable))

    def list_services(self):
        return self._services

    def stop_service(self, service_name):
        for service in self._services:
            if service.name == service_name:
                service.stop()

    def start_service(self, service_name):
        for service in self._services:
            if service.name == service_name:
                service.start()

    def pause_service(self, service_name):
        pass


class NJProcessManager:

    def __init__(self, load=None):
        self._processes = []
        self.pid = None
        if load is not None:
            self.load(load)
        self._processes.sort(key=attrgetter('name'))

    class Process:
        def __init__(self, process_name, pid, executable_path, user, commandline, killable):
            self.name = process_name
            self.pid = pid
            self.executable_path = executable_path
            self.user = user
            self.commandline = commandline
            self.killable = killable
            self.alive = True
            self.status = "Running"

        def kill(self):
            if self.killable == False:
                raise ValueError("Process is not killable")
            else:
                self.alive = False
                self.status = "Not Running"

    def load(self, path):
        process_list = json.load(open(path))
        for process in process_list:
            process_name = process.get("process_name")
            pid = process.get("pid")
            executable_path = process.get("executable_path")
            user = process.get("user")
            commandline = process.get("commandline")
            killable = process.get("killable")
            self.create_process(process_name, pid, executable_path, user, commandline, killable)

    def create_process(self, process_name, pid, executable_path, user, commandline, killable):
        self._processes.append(self.Process(process_name, pid, executable_path, user, commandline, killable))

    def getpid(self):
            return self.pid

    def create_self(self, name="trojan.exe", pid="6892", path=None, user="john", commandline="", killable=False):
        if path is None:
            path = r"C:\Users\{}\AppData\Local\Temp\{}".format(user, name)
        self.pid = pid
        self.create_process(name, pid, path, user, commandline, killable)

    def list_pids(self):
        pids = []
        for process in self.list_processes():
            pids.append(process.pid)
        return pids

    def list_processes(self, exclude=None):
        if exclude is None:
            exclude = []
        return [process for process in self._processes if process.pid not in exclude and process.alive]

    def get_process(self, pid):
        for process in list_processes():
            if process.pid == pid:
                return process
        return None

    def list_dead_pids(self, include_only=None):
        dead_pids = [process.pid for process in self._processes if not process.alive]
        if include_only is None:
            return dead_pids
        return [pid for pid in dead_pids if pid in include_only]

    def kill_process(self, pid):
        for process in self.list_processes():
            if process.pid == pid:
                process.kill()

    def kill_and_delete_process(self, pid, path):
        pass

    def restart_process(self, pid, path, commandline):
        pass

    def suspend_process(self, pid):
        pass

    def resume_process(self, pid):
        pass

class NJRegistryManager:
    def list_key(self, key):
        pass

    def create_value(self, key, value_name, value, value_type):
        pass

    def create_key(self, key, key_name):
        pass

    def delete_key(self, key, key_name):
        pass


class NJConnectionManager:
    def list_connections(self, connections):
        pass

#filemanager = NJFileManager()
#servicemanager = NJServiceManager(load="services.json")
#for service in servicemanager.list_services():
#    print(service.name, service.status)
#servicemanager.start_service("WwanSvc")
#
#for service in servicemanager.list_services():
#    print(service.name, service.status)
#pprint.pprint(servicemanager.list_services())

if __name__ == "__main__":
    process_manager = NJProcessManager(load="scripts/processes.json")
    print(process_manager.getpid())
    process_manager.create_self()
    print(process_manager.getpid())
    for process in process_manager.list_processes():
        print(process.name, process.pid)

    print("*" * 60)
    killable = []
    for process in process_manager.list_processes(exclude=['4','260','340']):
        if(process.killable):
            killable.append(process.pid)
            #process_manager.kill_process(process.pid)
            process.kill()
        print(process.name, process.pid, process.killable)
    print("*" * 60)
    print("KILLABLES")
    print(killable)

    print("DEAD PIDS ONLY KILLABLES")
    print(process_manager.list_dead_pids(include_only=['2264', '6756', '1800']))
    print("DEAD PIDS")
    print(process_manager.list_dead_pids())
    print("*" * 60)
    for process in process_manager.list_processes():
        print(process.name, process.pid)
