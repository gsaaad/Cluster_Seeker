import platform
def convert_path_format(path):
    """Convert path between Windows and Linux formats based on the current OS."""
    print("Path is: ", path)
    system = platform.system()
    print("System is: ", system)
    if system == "Windows":
        # If on Windows and given a Linux path (e.g., /nfs/turbo/lsa-adae/...), convert to Z:\ format
        if path.startswith('/nfs/turbo'):
            return path.replace('/nfs/turbo/lsa-adae', 'Z:').replace('/', '\\')
        return path.replace('/', '\\')
    else:  # Linux or other Unix-like
        # If given a Windows path starting with Z:, convert to Linux format
        if path.startswith('Z:'):
            # First, normalize backslashes to forward slashes
            path = path.replace('\\', '/')
            print("Path after replacing backslashes: ", path)
            # Then replace Z: with the Linux mount point, ensuring proper slash
            if path.startswith('Z:/'):
                return path.replace('Z:/', '/nfs/turbo/lsa-adae/')
            else:
                return path.replace('Z:', '/nfs/turbo/lsa-adae/')
        return path.replace('\\', '/')

path_test = r'Z:\migratedData\Lab\George\Python\George-Scripts\Cluster_Seeker'

print(convert_path_format(path_test)) # Expected: /nfs/turbo/lsa-adae/migratedData/Lab/George/Python/George-Scripts/Cluster_Seeker
