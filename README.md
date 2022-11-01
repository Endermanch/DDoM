# Daily Dose of Malware
A simple, open-source, easy to use, and free download manager for malware samples.

*Malware is art. Don't let it become a filthy criminal's tool.*

## Usage
As of now, the software is buggy but gets the job done.

Search syntax:

`filter:"value1,value2,value3..." limit:integer`

The limit keyword is optional: if you don't specify it, it will default to the value of **100**.
To begin the search, you must specify at least one filter.

| Filters   | Alias(-es)            | Represents      | Type        |
|-----------|-----------------------|-----------------|-------------|
| tag       | None                  | Tag             | "%s,%s,..." |
| signature | sig, sign             | Signature       | "%s,%s,..." |
| file_type | ft, type, filetype    | File Type       | "%s,%s,..." |
| hash      | sha, sha256, sha-256  | SHA-256         | "%s,%s,..." |
| limit     | None                  | Samples to find | "%d"        |

You may use filters themselves or their aliases as arguments in the search box.
Please note that the whitespace is treated as a separator and you must only use it in between the keywords.

<details>
  <summary>I didn't quite understand the types...</summary>
  <p>The types used in the table follow the printf standard, here's the basic list of them:</p>
  <table>
    <thead>
        <tr>
            <th>Identifier</th>
            <th>Type</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>%s</td>
            <td>string</td>
        </tr>
        <tr>
            <td>%d</td>
            <td>int</td>
        </tr>
        <tr>
            <td>%f</td>
            <td>float</td>
        </tr>
    </tbody>
</table>
</details>

## Interface
The interface will inevitably change, but the skeleton on the screenshot will remain the same.

![image](https://user-images.githubusercontent.com/44542704/199207421-a8163fab-6d4a-40b3-b2bc-0c21e01e5358.png)

## Requirements
Daily Dose of Malware is written in an interpretable language, therefore **crossplatform**. It was thoroughly tested only on Windows 10, but should run on any Linux distro and OSX just fine.
* Python 3.10 and higher
* Python dependencies (listed in requirements.txt):

  ```python
  import pyqt5
  import requests
  import threading
  import pyzipper
  import webbrowser
  import functools
  ```
* Basic safety precautions
  * Automatically unzip malicious samples **only** inside a sealed protected environment - Virtual Machine.
  * Keep zipped malicious samples in a safe corner, delete if you don't have any use for them.
  * **Sandboxes** are deceptively unsafe.
  * Isolated real hardware works well, make sure it's isolated though.
* Basic technical skills :wink:

## Known bugs
- [ ] Sorting for non-string values is broken
- [ ] Cancel button sets half-found search results  
- [ ] Application crashes while parsing huge chunks of data

## Contributing
In case you find a bug in the software, hit me up in the **issues**. Make sure to articulate the issue well and if you have enough Python knowledge, suggest a way to fix it.
Thank you.

**I don't accept pull requests**, because this project is my university assignment for 2 semesters.

## Resources
The best cherry-picked samples are stored in my [Malware Database](http://github.com/Endermanch/MalwareDatabase "Malware Database").

My [Website](http://malwarewatch.org "MalwareWatch")<br>
My [YouTube](http://youtube.com/endermanch "YouTube")<br>
My [Twitter](http://twitter.com/endermanch "Twitter")

Contact e-mail: realendermanch@gmail.com
