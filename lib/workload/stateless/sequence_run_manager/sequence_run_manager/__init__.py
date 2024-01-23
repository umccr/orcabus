import pymysql

# see https://github.com/PyMySQL/PyMySQL/issues/790
pymysql.version_info = (1, 4, 6, "final", 0)
pymysql.install_as_MySQLdb()
