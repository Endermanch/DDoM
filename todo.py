# ideas:
# unzip on demand - password infected
# download from multiple sources
# progress bar
# help inside about
# tag:"Adware", hash:"j08923r0239fjoubfouwfj9023j"
# include short setup inside file
# classes:
# filemanager
# downloadmanager
# probably malware class

# save this file for 4th term practice - can show this to the workplace

# Bazaar - use mainly POST requests

            # To download:
            # 'query': 'get_file',
            # 'sha256_hash': 'hash'
            # query_status: illegal_sha256_hash, no_sha256_hash, file_not_found

            # To query by tag, use the following:
            # 'query': 'get_taginfo',
            # 'hash': 'necessary SHA256, SHA1 or MD5 hash',
            # query_status: hash_not_found, illegal_hash, no_hash_provided

            # To query by tag, use the following:
            # 'query': 'get_taginfo',
            # 'tag': 'Adware',
            # 'limit': 100 - UP TO A 1000 (default 100)
            # query_status: illegal_tag, no_tag_provided, tag_not_found, no_results

            # To query by signature, use the following:
            # 'query': 'get_siginfo',
            # 'signature': 'Adware',
            # 'limit': 100 - UP TO A 1000 (default 100)
            # query_status: illegal_signature, no_signature_provided, signature_not_found, no_results

            # To query by file type, use the following:
            # 'query': 'get_file_type',
            # 'file_type': 'exe',
            # 'limit': 100 - UP TO A 1000 (default 100)
            # query_status: illegal_file_type, no_file_type, no_results

            # Response codes I will use:
            # response.file_type
            # response.file_name
            # response.signature
            # response.first_seen
            # response.last_seen
            # response.md5_hash
            # response.sha256_hash
            # response.intelligence.downloads
            # response.intelligence.uploads

            # Query latest malware samples:
            # 'query': 'get_recent',
            # 'selector': 'time' - get additions within the past 60 minutes
            # 'selector': '100' - get latest 100 additions
            # query_status: ok, no_selector, unknown_selector, no_results

            # Daily malware batches:
            # https://datalake.abuse.ch/malware-bazaar/daily/YYYY-MM-DD.zip (up to a gigabyte worth of data), it takes a few minutes to generate the daily batch

            # MalShare - use mainly GET requests

# It's bad for now, after I add file types and more it won't be
            # thread_name = threading.current_thread().name
            # self.app.responses[thread_name] = None
            # self.app.showMessageBox.emit(
            #    thread_name,
            #    'critical',
            #    'Error',
            #    f'Please input a tag to search for.\nSent from thread {format(thread_name)}'
            #)

            # while self.app.responses[thread_name] is None:
            #    time.sleep(0.1)

            # print('Thread {} got response from message box: {}'.format(thread_name, self.app.responses[thread_name]))