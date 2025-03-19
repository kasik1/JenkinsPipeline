Role Name
=========

Automate Venafi Certificates creation and installation.


Notes
------------

When requesting certificates, we might need with manual approval sometime. That is not the case right now, so this code is left just as a reminder
```
- name: If MultiSAN cert, provide warning to user
  pause:
    seconds: 30
    prompt: This certificate may require manual workflow approval from CIP before being processed. If your retrieve fails, this is a potential cause.
  when:
    - "'MultiSAN' in cert_bucket."
 ```
Also, if dealing with sans names, this must be included in request_payload.json.j2
 ```
{% if additional_sans is defined %}
{% for san in additional_sans %}
    { "Type": 2, "Name": "{{ san | lower }}" },
{% endfor %}
{% endif %}
 ```


Something similar happens when dealing with certificates not provided by the Microsoft Autorithy (MSCA)
````
- name: If certificate is Internal Production (but not MSCA), set Cygnacom string
  set_fact:
    cygnacom_string: "{{ cygnacom_driver_strings.prod }}"
  when:
    - "'Internal' in cert_bucket"
    - "'Production' in cert_bucket"
    - "not 'MSCA' in cert_bucket"

- name: If certificate is Internal Test (but not MSCA), set Cygnacom string
  set_fact:
    cygnacom_string: "{{cygnacom_driver_strings.test }}"
  when:
    - "'Internal' in cert_bucket"
    - "'Test' in cert_bucket"
    - "not 'MSCA' in cert_bucket"
```
Again, add this to custom_fields.json.j2
```
{% if cygnacom_string is defined %}
    {
      "ItemGuid": "{4c01c9b3-aebd-41b1-80ba-f736b264dfcc}",
      "List": ["{{ cygnacom_string }}"]
    },
{% endif %}
```

Requirements
------------

None

Role Variables
--------------

service_account
service_account_password

Dependencies
------------

None

Example Playbook
----------------

For running the playbook inside your machine:
 ```
 $ ansible-playbook -vvv -K venafi_certificates.yml --extra-vars "ndoportal_environment=dev" --vault-password-file vault_id
 ```

 To include the install task in a playbook to run during a pipeline:
 ```
- name: install certificate from venafi
  include_role:
    name: venafi_certificates
    tasks_from: install

 ```

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:


License
-------

BSD

Author Information
------------------

Patricio parga (eduaro.parga@cigna.com)
