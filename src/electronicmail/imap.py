from __future__ import annotations

import sys
import os
import importlib.metadata
import argparse
import textwrap
import getpass # .getuser
import copy # .deepcopy
import json # .dump
            # .load
import ssl # .create_default_context
import pprint # .pprint
import email.parser # .BytesParser
                    #             .parsebytes
import email.message # .Message
import email.header # .decode_header
import email.policy # .default
import imaplib

import bs4 # .BeautifulSoup

from . import meta # .get_meta_str


class _Conf:
    """
    Class to represent an IMAP client configuration file
    """

    _CONF_DEFAULT_DICT = {
        'host'     : 'host goes here',
        'port'     : 0000,
        'user'     : 'user goes here',
        'password' : 'password goes here'
    }

    def __init__(self : _Conf) -> _Conf:
        
        home_dir_path = f'/home/{getpass.getuser()}'

        assert os.path.isdir(home_dir_path), home_dir_path

        conf_dir_path = os.path.join(home_dir_path, '.electronicmail')

        if not os.path.isdir(conf_dir_path):

            os.mkdir(conf_dir_path, mode=0o700)

        conf_file_path = os.path.join(conf_dir_path, 'imap.json')

        if not os.path.isfile(conf_file_path):

            conf_default_dict = copy.deepcopy(_Conf._CONF_DEFAULT_DICT)

            conf_file_obj = open(conf_file_path, mode='w')

            json.dump(obj=conf_default_dict, fp=conf_file_obj, indent=4)

            conf_file_obj.close()

        assert os.path.isfile(conf_file_path)

        os.chmod(path=conf_file_path, mode=0o600)

        conf_file_obj = open(conf_file_path, 'r')

        conf_dict = json.load(fp=conf_file_obj)

        conf_file_obj.close()

        for key, value_default in _Conf._CONF_DEFAULT_DICT.items():

            assert key in conf_dict, key

            if conf_dict[key] == value_default:

                sys.stderr.write(
                    textwrap.dedent(
                        f'''\
                        conf file path : {conf_file_path}
                            please update default
                            {key} : {value_default}
                        '''
                    )
                )

        self.host     = conf_dict['host']
        self.port     = conf_dict['port']
        self.user     = conf_dict['user']
        self.password = conf_dict['password']


class Client:
    """
    IMAP client
    """

    def __init__(self : Client) -> Client:
    
        self._conf = _Conf()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        print('#connect')
        self._kernel = imaplib.IMAP4_SSL(
            host        = self._conf.host,
            port        = self._conf.port,
            ssl_context = ssl_context
        )

        print('#login')
        print(
            self._kernel.login(
                user     = self._conf.user,
                password = self._conf.password
            )
        )

    # =====
    # 6.3.1
    # =====
    #
    # https://datatracker.ietf.org/doc/html/rfc2060.html#section-6.3.1
    #
    # https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.select
    # 
    def select(self : Client, mailbox_name : str):
        """
        SELECT Command

        Arguments:  mailbox name

        Responses:  REQUIRED untagged responses: FLAGS, EXISTS, RECENT
                    OPTIONAL OK untagged responses: UNSEEN, PERMANENTFLAGS

        Result:     OK - select completed, now in selected state
                    NO - select failure, now in authenticated state: no
                         such mailbox, can't access mailbox
                    BAD - command unkown or arguments invalid

        The SELECT command selects a mailbox so that messages in the
        mailbox can be accessed.  Before returning an OK to the client,
        the server MUST send the following untagged data to the client:

           FLAGS       Defined flags in the mailbox.  See the description
                       of the FLAGS response for more detail.

           <n> EXISTS  The number of messages in the mailbox.  See the
                       description of the EXISTS response for more detail.

           <n> RECENT  The number of messages with the \Recent flag set.
                       See the description of the RECENT response for more
                       detail.

           OK [UIDVALIDITY <n>]
                       The unique identifier validity value.  See the
                       description of the UID command for more detail.

        to define the initial state of the mailbox at the client.

        The server SHOULD also send an UNSEEN response code in an OK
        untagged response, indicating the message sequence number of the
        first unseen message in the mailbox.

        If the client can not change the permanent state of one or more of
        the flags listed in the FLAGS untagged response, the server SHOULD
        send a PERMANENTFLAGS response code in an OK untagged response,
        listing the flags that the client can change permanently.

        Only one mailbox can be selected at a time in a connection;
        simultaneous access to multiple mailboxes requires multiple
        connections.  The SELECT command automatically deselects any
        currently selected mailbox before attempting the new selection.
        Consequently, if a mailbox is selected and a SELECT command that
        fails is attempted, no mailbox is selected.
        """
        result, responses = self._kernel.select(
            mailbox  = mailbox_name,
            readonly = False
        )
        return result, responses
        
    # =====
    # 6.3.8
    # =====
    #
    # Actually we want section 6.3.8, but link is broken so we point to 6.3.7:
    #
    #   https://datatracker.ietf.org/doc/html/rfc2060.html#section-6.3.7
    #
    #   https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.list
    #
    def list(
        self                                 : Client,
        reference_name                       : str,
        mailbox_name_with_possible_wildcards : str
    ):
        """
        Arguments:  reference name
                    mailbox name with possible wildcards
     
        Responses:  untagged responses: LIST
     
        Result:     OK - list completed
                    NO - list failure: can't list that reference or name
                    BAD - command unknown or arguments invalid

        The LIST command returns a subset of names from the complete set
        of all names available to the client.  Zero or more untagged LIST
        replies are returned, containing the name attributes, hierarchy
        delimiter, and name; see the description of the LIST reply for
        more detail.
        """

        """
        List mailbox names in reference_name (a directory) that matches
        mailbox_name_with_possible_wildcards (a pattern).
        In order to list the contents of the top-level / root mail folder,
        reference_name must be a str that contains two empty double quotes ('""')
        """
        result, responses = self._kernel.list(
            directory = reference_name,                      # str
            pattern   = mailbox_name_with_possible_wildcards # str
        )
        assert result in ['OK', 'NO', 'BAD'], result
        assert isinstance(responses, list), type(responses)

        mailboxes = list()

        for resp in responses:

            name_attributes = set()
            hierarchy_delimeter = None
            name = None

            assert isinstance(resp, bytes)

            i = 0
            state = 'INIT'
            
            name_attribute_begin_index = None
            hierarchy_delimiter_begin_index = None
            name_begin_index = None

            while True:

                assert 0 <= i and i <= len(resp)

                if 'INIT' == state:

                    assert 0 == i
                    assert b'(' == resp[i:i+1]

                    state = 'READ_NAME_ATTRIBUTE_BEGIN'
                    i = 1

                elif 'READ_NAME_ATTRIBUTE_BEGIN' == state:

                    assert 0 < i and i < len(resp)
                    assert b'\\' == resp[i:i+1]

                    assert None == name_attribute_begin_index
                    name_attribute_begin_index = i

                    state = 'READ_NAME_ATTRIBUTE_INSIDE'
                    i += 1

                elif 'READ_NAME_ATTRIBUTE_INSIDE' == state:

                    assert 0 < i and i < len(resp)

                    if resp[i:i+1] in [b' ', b')']:

                        name_attr = resp[name_attribute_begin_index:i]

                        assert name_attr not in name_attributes

                        name_attributes.add(name_attr)

                        name_attribute_begin_index = None

                        if b' ' == resp[i:i+1]:

                            state = 'READ_NAME_ATTRIBUTE_BEGIN'
                            i += 1

                        elif b')' == resp[i:i+1]:

                            assert b' ' == resp[i+1:i+2]
                            assert b'"' == resp[i+2:i+3]

                            assert None == hierarchy_delimiter_begin_index
                            hierarchy_delimiter_begin_index = i+3

                            state = 'READ_HIERARCHY_DELIMITER_INSIDE'
                            i += 3

                    else:
                        i += 1

                elif 'READ_HIERARCHY_DELIMITER_INSIDE' == state:

                    assert 0 < i and i < len(resp)

                    if b'"' == resp[i:i+1]:

                        assert b' ' == resp[i+1:i+2]
                        assert b'"' == resp[i+2:i+3]

                        assert None == hierarchy_delimeter
                        hierarchy_delimiter = resp[hierarchy_delimiter_begin_index:i]
                        hierarchy_delimiter_begin_index = None

                        assert None == name_begin_index
                        name_begin_index = i+3

                        state = 'READ_NAME_INSIDE'
                        i += 3

                    else:
                        i += 1

                elif 'READ_NAME_INSIDE' == state:

                    assert 0 < i and i < len(resp)

                    if b'"' == resp[i:i+1]:

                        assert i+1 == len(resp)

                        assert None == name
                        name = resp[name_begin_index:i]
                        name_begin_index = None

                        state = 'DONE'
                        i += 1

                    else:
                        i += 1

                elif 'DONE' == state:

                    assert i == len(resp)
                    break

            assert None == name_attribute_begin_index
            assert None == hierarchy_delimiter_begin_index
            assert None == name_begin_index

            mailboxes.append({
                'name_attributes'     : name_attributes,
                'hierarchy_delimiter' : hierarchy_delimiter,
                'name'                : name
            })

        return result, mailboxes


    # =================
    # 6.3.11 (RFC 9051)
    # =================
    #
    # https://datatracker.ietf.org/doc/html/rfc9051#section-6.3.11
    #
    # https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.status
    #
    # https://github.com/python/cpython/blob/3.13/Lib/imaplib.py#L832-L841
    #
    def status(
        self                        : Client,
        mailbox_name                : str,
        status_data_item_names_list : list[str]
    ):
        """
        Arguments:    mailbox name

                      status data item names

        Responses:    REQUIRED untagged responses:  STATUS

        Result:       OK -  status completed
                      NO -  status failure: no status for that name
                      BAD -  command unknown or arguments invalid

        The STATUS command requests the status of the indicated mailbox.  It
        does not change the currently selected mailbox, nor does it affect
        the state of any messages in the queried mailbox.

        The STATUS command provides an alternative to opening a second
        IMAP4rev2 connection and doing an EXAMINE command on a mailbox to
        query that mailbox's status without deselecting the current mailbox
        in the first IMAP4rev2 connection.
     
        Unlike the LIST command, the STATUS command is not guaranteed to be
        fast in its response.  Under certain circumstances, it can be quite
        slow.  In some implementations, the server is obliged to open the
        mailbox as "read-only" internally to obtain certain status
        information.  Also unlike the LIST command, the STATUS command does
        not accept wildcards.
     
           Note: The STATUS command is intended to access the status of
           mailboxes other than the currently selected mailbox.  Because the
           STATUS command can cause the mailbox to be opened internally, and
           because this information is available by other means on the
           selected mailbox, the STATUS command SHOULD NOT be used on the
           currently selected mailbox.  However, servers MUST be able to
           execute the STATUS command on the selected mailbox.  (This might
           also implicitly happen when the STATUS return option is used in a
           LIST command.)
     
           The STATUS command MUST NOT be used as a "check for new messages
           in the selected mailbox" operation (refer to Sections 7 and 7.4.1
           for more information about the proper method for new message
           checking).
     
           STATUS SIZE (see below) can take a significant amount of time,
           depending upon server implementation.  Clients should use STATUS
           SIZE cautiously.
     
        The currently defined status data items that can be requested are:
     
        MESSAGES
           The number of messages in the mailbox.
     
        UIDNEXT
           The next unique identifier value of the mailbox.  Refer to
           Section 2.3.1.1 for more information.
     
        UIDVALIDITY
           The unique identifier validity value of the mailbox.  Refer to
           Section 2.3.1.1 for more information.
     
        UNSEEN
           The number of messages that do not have the \Seen flag set.
     
        DELETED
           The number of messages that have the \Deleted flag set.
     
        SIZE
           The total size of the mailbox in octets.  This is not strictly
           required to be an exact value, but it MUST be equal to or greater
           than the sum of the values of the RFC822.SIZE FETCH message data
           items (see Section 6.4.5) of all messages in the mailbox.
     
        Example:
     
          C: A042 STATUS blurdybloop (UIDNEXT MESSAGES)
          S: * STATUS blurdybloop (MESSAGES 231 UIDNEXT 44292)
          S: A042 OK STATUS completed
        """
        assert isinstance(mailbox_name, str)
        assert isinstance(status_data_item_names_list, list)

        for name in status_data_item_names_list:
            assert isinstance(name, str)
            assert name in [
                'MESSAGES',
                'UIDNEXT'
                'UIDVALIDITY',
                'UNSEEN',
                'DELETED',
                'SIZE'
            ]

        status_data_item_names_str = \
            '(' + ' '.join(status_data_item_names_list) + ')'

        result, response = self._kernel.status(
            mailbox = mailbox_name,
            names   = status_data_item_names_str
        )
        
        assert result in ['OK', 'NO', 'BAD']

        return result, response
        

    # ================
    # 6.4.3 (RFC 9051)
    # ================
    #
    # https://datatracker.ietf.org/doc/html/rfc9051#section-6.4.3
    #
    # https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.expunge
    #
    # https://github.com/python/cpython/blob/3.13/Lib/imaplib.py#L523-L534
    #
    def expunge(self : Client):
        """
        Arguments:    none

        Responses:    untagged responses:  EXPUNGE

        Result:       OK -  expunge completed
                      NO -  expunge failure: can't expunge (e.g., permission
                         denied)
                      BAD -  command unknown or arguments invalid

        The EXPUNGE command permanently removes all messages that have the
        \Deleted flag set from the currently selected mailbox.  Before
        returning an OK to the client, an untagged EXPUNGE response is sent
        for each message that is removed.

        Example:

          C: A202 EXPUNGE
          S: * 3 EXPUNGE
          S: * 3 EXPUNGE
          S: * 5 EXPUNGE
          S: * 8 EXPUNGE
          S: A202 OK EXPUNGE completed

        Note: In this example, messages 3, 4, 7, and 11 had the \Deleted flag
        set.  See the description of the EXPUNGE response (Section 7.5.1) for
        further explanation.
        """
        result, responses = self._kernel.expunge()
        assert result in ['OK', 'NO', 'BAD']
        return result, responses
        

    # =====
    # 6.4.4
    # =====
    #
    # https://www.rfc-editor.org/rfc/rfc9051.html#section-6.4.4
    #
    # https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.search
    #
    # https://github.com/python/cpython/blob/3.13/Lib/imaplib.py#L720-L735
    #
    # 
    def search(
        self                           : Client,
        optional_charset_specification : str       = None,
        one_or_more_searching_criteria : list[str] = []
    ):
        result, response = self._kernel.search(
            optional_charset_specification,
            *one_or_more_searching_criteria
        )
        assert result in ['OK', 'NO', 'BAD'], result
        assert isinstance(response, list)
        assert 1 == len(response)
        assert isinstance(response[0], bytes)
        message_numbers = response[0].decode('utf-8').split()

        return result, message_numbers


    # =====
    # 6.4.5
    # =====
    #
    # https://datatracker.ietf.org/doc/html/rfc9051#section-6.4.5
    #
    # https://github.com/python/cpython/blob/3.13/Lib/imaplib.py#L537-L549
    #
    # 
    def fetch(
        self                             : Client,
        sequence_set                     : str,
        message_data_item_names_or_macro : str
    ):
        """
        Arguments:  sequence set
                    message data item names or macro

         Responses:  untagged responses: FETCH

         Result:     OK - fetch completed
                     NO - fetch error: can't fetch that data
                     BAD - command unknown or arguments invalid
        """
        result, response = self._kernel.fetch(
            message_set   = sequence_set,
            message_parts = message_data_item_names_or_macro
        )
        return result, response


    def fetch_and_print_headers(
        self           : Client,
        sequence_set   : str,
        print_all_keys : bool = False
    ):
        print(f'FETCH {sequence_set} (FLAGS)')
        result, response = self.fetch(
            sequence_set                     = sequence_set,
            message_data_item_names_or_macro = '(FLAGS)'
        )
        print(f'    result  : {result}')            
        print(f'    reponse : {response}')
        del result
        del response
        
        print(f'FETCH {sequence_set} (RFC822.HEADER)')
        result, untagged_responses = self.fetch(
            sequence_set                     = sequence_set,
            message_data_item_names_or_macro = '(RFC822.HEADER)'
        )
    
        #print(f'  result  : {result}')
        #         Subject :
    
        bytes_parser = email.parser.BytesParser()
    
   
        assert isinstance(untagged_responses, list)
        assert 2 == len(untagged_responses)
    
        assert isinstance(untagged_responses[0], tuple)
        assert 2 == len(untagged_responses[0])
    
        assert isinstance(untagged_responses[0][0], bytes)
        assert isinstance(untagged_responses[0][1], bytes) # <= the actual headers
    
        assert isinstance(untagged_responses[1], bytes)
        assert b')' == untagged_responses[1]
    
        header_bytes = untagged_responses[0][1]
    
        header_obj = bytes_parser.parsebytes(header_bytes, headersonly=True)
    
        # print(f'type(header_obj) : {type(header_obj)}')
    
        # for k in header_obj.keys():
        #     print(k)

        subject = header_obj['Subject']

        if '=?' == subject[:2]:

            subject = email.header.decode_header(subject)
    
            subject = subject[0][0].decode(subject[0][1])

        else:
            pass

        print(f'  To      : {header_obj["To"]}')
        print(f'  From    : {header_obj["From"]}')
        #print(f'  Subject : {header_obj["Subject"]}')
        print(f'  Subject : {subject}')
        print(f'  Date    : {header_obj["Date"]}')
    
        if print_all_keys:
            for k in header_obj.keys():
                print(k)
    
        # import code
        # code.interact(local=locals())


    # ================
    # 6.4.6 (RFC 9051)
    # ================
    #
    # https://datatracker.ietf.org/doc/html/rfc9051#section-6.4.6
    #
    # https://docs.python.org/3/library/imaplib.html#imaplib.IMAP4.store
    #
    # https://github.com/python/cpython/blob/3.13/Lib/imaplib.py#L844-L852
    #
    #
    # legal values for sequence_set are defined in RFC 9051 Section 4.1.1.
    #
    def store(
        self                        : Client,
        sequence_set                : str,
        message_data_item_name      : str,
        value_for_message_data_item : str
    ):
        """
        Arguments: sequence set
                   message data item name
                   value for message data item

        Responses: untagged responses: FETCH

        Result   : OK  - store completed
                   NO  - store error: can't store that data
                   BAD - command unkown or arguments invalid
        """
        result, response = self._kernel.store(
            message_set = sequence_set,
            command     = message_data_item_name,
            flags       = value_for_message_data_item
        )
        assert result in ['OK', 'NO', 'BAD']
        return result, response
        


def _interact(args : argparse.Namespace) -> int:

    connection = connect()
    
    while True:
        command = input('imap> ')
        
        command_components = command.split()
        

        error = False
        
        if 0 == len(command_components):
            
            pass

        else:
            assert 0 < len(command_components)

            cmd  = command_components[0]
            args = command_components[1:]

            # for i in range(len(args)):
            #     if '""' == args[i]:
            #         args[i] = ''
            #     elif '"*"' == args[i]:
            #         args[i] = '*'
            for i in range(len(args)):
                args[i] = args[i].replace('"', '')

            print(f'cmd  : {cmd}')
            print(f'args : {args}')

            if 'list' == cmd:

                if 2 != len(args):

                    error = True

                else:

                    _list(
                        imap                                 = imap,
                        reference_name                       = args[0],
                        mailbox_name_with_possible_wildcards = args[1]
                    )

            elif 'status' == cmd:

                if len(args) < 2:
                    error = True
                else:
                    _status(
                        imap                   = imap,
                        mailbox_name           = args[0],
                        status_data_item_names = args[1:]
                    )
            
            elif 'search' == cmd:

                if 0 == len(args):
                    error = True
                else:
                    _search(
                        imap                           = imap,
                        optional_charset_specification = None,
                        one_or_more_searching_criteria = args
                    )

            #elif 'uid' == cmd:

            #    if 0 == len(args):
            #        error = True
            #    else:
            #        uid(client=client, args=args)

            elif 'fetch' == cmd:

                if 2 != len(args):
                    error = True
                else:
                    _fetch(
                        imap                             = imap,
                        message_set                      = args[0],
                        message_data_item_names_or_macro = args[1:]
                    )

            elif 'fetch-header' == cmd:

                if 1 != len(args):
                    error = True
                else:
                    _fetch_header(
                        imap       = imap,
                        message_id = args[0]
                    )

            elif 'fetch-header-keys' == cmd:

                if 1 != len(args):
                    error = True
                else:
                    _fetch_header(
                        imap           = imap,
                        message_id     = args[0],
                        print_all_keys = True
                    )

            elif cmd in ['logout', 'q', 'quit', 'disconnect', 'exit']:

                break

            elif 'select' == cmd:

                if 1 != len(args):
                    error = True
                else:
                    _select(
                        imap         = imap,
                        mailbox_name = args[0]
                    )

            elif 'store' == cmd:

                if 3 != len(args):
                    error = True
                else:
                    _store(
                        imap                        = imap,
                        message_set                 = args[0],
                        message_data_item_name      = args[1],
                        value_for_message_data_item = args[2]
                    )

            elif 'check' == cmd:

                if 0 != len(args):
                    error = True
                else:
                    _check(imap=imap)

            elif 'expunge' == cmd:

                if 0 != len(args):
                    error = True
                else:
                    _expunge(imap=imap)

            else:
                error = True



        if error:
            print(
                textwrap.dedent(
                    f'''\
                    '{command}' is either an unrecognized command or was used improperly;
                      legal command usages are:
                         list <reference_name> <mailbox_name_with_possible_wildcards>
                         select <folder>
                         status <folder>
                         quit

                    cmd  : {cmd}
                    args : {args}'''
                ),
                file = sys.stderr
            )



    return 0


def _test(args : argparse.Namespace) -> int:
    '''
    Check whether we can connect to the IMAP server and perform
    some basic operations.
    '''

    client = Client()


    reference_name = '""'
    mailbox_name_with_possible_wildcards = '*'

    print(f'LIST {reference_name} {mailbox_name_with_possible_wildcards}')

    result, mailboxes = client.list(
        reference_name                       = reference_name,
        mailbox_name_with_possible_wildcards = mailbox_name_with_possible_wildcards
    )
    print(f'result         : {result}')
    print(f'len(mailboxes) : {len(mailboxes)}')
    
    print('\n====')
    for mb in mailboxes:
        print('name :', ''.join([chr(b) for b in mb['name']]))
        print('    attributes : ', mb['name_attributes'])
        print('    delim      : ', mb['hierarchy_delimiter'])
    print('====\n')



    mailbox_name = 'Spam'

    print(f'SELECT {mailbox_name}')

    result, responses = client.select(mailbox_name=mailbox_name)
    sys.stderr.write(
        textwrap.dedent(
            f'''\
            result    : {result}
            responses : {responses}
            '''
        )
    )
    
    result, message_numbers = client.search(
        optional_charset_specification = None,
        one_or_more_searching_criteria = ['ALL']
    )
    
    print()
    print( 'SEARCH ALL')
    print(f'    result          : {result}')
    print(f'    message_numbers : {message_numbers}')
    
    for msg_num in message_numbers:
        client.fetch_and_print_headers(
            sequence_set   = msg_num,
            print_all_keys = False
        )
    

    delete_message = input('delete message with sequence number 1 (yes/no)? > ')

    if 'yes' == delete_message:

        print('\nSTORE +FLAGS (\\Deleted)')
        result, response = client.store(
            sequence_set                = message_numbers[0],
            message_data_item_name      = '+FLAGS',
            value_for_message_data_item = '\\Deleted'
        )
        print(f'    result   : {result}')
        print(f'    response : {response}')

        client.fetch_and_print_headers(
            sequence_set   = message_numbers[0],
            print_all_keys = False
        )

        print('\nEXPUNGE')
        result, responses = client.expunge()
        print(f'    result    : {result}')
        print(f'    responses : {responses}')


        result, message_numbers = client.search(
            optional_charset_specification = None,
            one_or_more_searching_criteria = ['ALL']
        )

        print()
        print( 'SEARCH ALL')
        print(f'    result          : {result}')
        print(f'    message_numbers : {message_numbers}')
        
        for msg_num in message_numbers:
            client.fetch_and_print_headers(
                sequence_set   = msg_num,
                print_all_keys = False
            )
    
    else:
        print(f'you entered "{delete_message}"; no delete')


    print(f'\nFETCH {message_numbers[0]} (RFC822)')
    result, response = client.fetch(
        sequence_set                     = message_numbers[0],
        message_data_item_names_or_macro = '(RFC822)'
    )
    print(f'    result : {result}')

    raw_email = response[0][1]

    # Parse the raw email into a Python object
    email_message = email.message_from_bytes(
        raw_email,
        policy = email.policy.default
    )
    
    # Print the subject of the email
    print("Subject:", email_message['Subject'])

    print_email_body = input('print the email body (yes/no) > ')

    if 'yes' == print_email_body:
    
        # If the email has multiple parts, iterate through them
        if email_message.is_multipart():
            for part in email_message.iter_parts():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
        
                # Extract the body
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode()
                    print("Body:", body)
            
            print('================================')
            print('email message has MULTIPLE parts')
        else:
            # If the email is not multipart, just get the payload
            body = email_message.get_payload(decode=True).decode()

            if 'text/html' == email_message.get_content_type():

                soup = bs4.BeautifulSoup(body, 'html.parser')
                body = soup.get_text()

            print("Body")
            print('====')
            print(body)

            print('==========================')
            print('email message has ONE part')

    else:
        print(f'you entered "{print_email_body}"; will not print email body')




    return 0


def _conf(args : argparse.Namespace) -> int:
    '''
    Generate the configuration file.
    '''
   
    _Conf()

    return 0


def _hello(args : argparse.Namespace) -> int:
    '''
    Print the hello world program to stdout.
    '''
    
    this_file_path = __file__
    
    assert 'imap.py' == os.path.basename(this_file_path)

    package_module_dir_path = os.path.dirname(this_file_path)

    data_dir_path = os.path.join(package_module_dir_path, 'data')

    assert os.path.isdir(data_dir_path)

    quote_file_path = os.path.join(data_dir_path, 'quote.txt')

    assert os.path.isfile(quote_file_path)

    with open(quote_file_path, 'r') as quote_file:

        quote_str = quote_file.read().strip()

    print(quote_str)

    return 0


def main() -> int:

    assert 'NAME' not in globals()

    exec(meta.get_meta_str())

    assert 'NAME' in globals()

    metadata = None
    try:
        metadata = importlib.metadata.metadata(NAME)
    except importlib.metadata.PackageNotFoundError:
        pass

    name    = metadata['Name']    if metadata else 'name_not_available'
    summary = metadata['Summary'] if metadata else 'summary_not_available'
    version = metadata['Version'] if metadata else 'version_not_available'

    assert NAME == name, \
        textwrap.dedent(
            f'''
            NAME : {NAME}
            name : {name}'''
        )

    assert 'electronicmail' == name

    name = f'{name}.imap'

    assert 'electronicmail.imap' == name

    parser = argparse.ArgumentParser(
        prog                  = name,
        description           = summary,
        formatter_class       = argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars = '@'
    )
    
    parser.add_argument(
        '-V', '--version',
        action  = 'version',
        version = f'{name} {version}'
    )

    subparsers = parser.add_subparsers(required=True)

    hello_subparser = subparsers.add_parser('hello')
    hello_subparser.set_defaults(func=_hello)

    conf_subparser = subparsers.add_parser('conf')
    conf_subparser.set_defaults(func=_conf)

    test_subparser = subparsers.add_parser('test')
    test_subparser.set_defaults(func=_test)

    interact_subparser = subparsers.add_parser('interact')
    interact_subparser.set_defaults(func=_interact)
    
    args = parser.parse_args()

    return args.func(args)



if '__main__' == __name__:
    sys.exit(main())




