# ipf-xsede %VER%-%REL%
# Generic Publisher Instructions  
## What is the Generic Publisher?

IPF is usually configured to run workflows that dynamically gather specific information and publish it in a
predefined format. For example, the Software Modules and Batch System workflows gather information from module
files and the batch scheduler and publish it in a standard GLUE2 JSON schema format.

The Generic Publisher introduced with IPF-1.7 reads a JSON file and publishes it without modification. Thus it
can publish any information generated asynchronously by any program separately from IPF, and enables publishing
new information without having to install a new IPF that includes built-in workflows to generate the information.

## Configuring the Generic Publisher

Let's say one wants to publish filesystem information in a <data_path>/filesystems_data.json file:

 1. Copy the etc/ipf/workflow/template/generic_publish.json workflow configuration template to etc/ipf/workflow/filesystems.json
 2. Edit filesystems.json and give you workflow a "name" and "description"
 3. Set <RESOURCE_ID> to the RDR Resource ID of the resource the information is about
 4. Set <FULL_QUALIFIED_JSON_FILE_PATH> to the <data_path>/filesystems_data.json file path
 5. Set <EXCHANGE>, <USERNAME>, and <PASSWORD> appropriately for the AMQP services you are publishing to

Your new etc/ipf/workflow/filesystems.json configuration can be used to publish your filesystems_data.json file

$ ipf_workflow $IPF_ETC_PATH/workflow/filesystems.json

## Additional Considerations

Before publishing new information to an AMQP service, AMQP needs to be configured to accept and process that
information. Only configure the Generic Publisher in coordination with the AMQP service operator and use the
<EXCHANGE> you are given and a <RESOURCE_ID> that identifies what resource the information is about.
