import sqlite3
import json
import datetime

class StatusDAO(object):

    def __init__(self, db):
        self.db_conn = sqlite3.connect(db, check_same_thread=False)

    def add_host(self, host_name, ip, job_name, region, creation_time, role):
        cursor = self.db_conn.cursor()

        try:
            query = '''INSERT INTO cluster_status (host_name, ip, region, job_name, creation_time, status, role) VALUES (?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(query, (host_name, ip, region, job_name, creation_time, 'RUNNING', role))
            self.db_conn.commit()
        except Exception as e:
            print "An error occured when adding server to DB:", e
            self.db_conn.rollback()
        finally:
            cursor.close()

    def update_entry(self, host_name, status, termination_time, revoked=None):
        cursor = self.db_conn.cursor()

        try:
            if not revoked:
                query = '''UPDATE cluster_status SET status=?, termination_time=? WHERE host_name=?'''
                cursor.execute(query, (status, termination_time, host_name))
                self.db_conn.commit()
            else:
                query = '''UPDATE cluster_status SET status=?, termination_time=?, revoked=? WHERE host_name=?'''
                cursor.execute(query, (status, termination_time, revoked, host_name))
                self.db_conn.commit()
        except Exception as e:
            print "An error occured when updating server in DB:", e
            self.db_conn.rollback()
        finally:
            cursor.close()

    def select_running_host_by_region(self, job_name, region, status, role=None):
        cursor = self.db_conn.cursor()

        try:
            if role:
                query = '''SELECT * FROM cluster_status WHERE job_name=? AND region=? AND status=? AND role=?'''
                cursor.execute(query, (job_name, region, status ,role,))
            else:
                query = '''SELECT * FROM cluster_status WHERE job_name=? AND region=? AND status=?'''
                cursor.execute(query, (job_name, region, status,))
            all_rows = cursor.fetchall()
        except Exception as e:
            print "An error occured when selecting server in DB:", e
            self.db_conn.rollback()
        finally:
            cursor.close()
            return all_rows