
# CDK Python project usage

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  
## Local Setup

This project utilizes python and poetry. It assumes that these 2 pre-requisites are installed.

To initialize the environment to run this sample:

```
$ make init
```

It is also necessary to have an AWS Account Region that is bootstrapped to run CDK. 

```
$ make bootstrap
```

NOTE: In `app.py`, you will need to replace `<SOME VPC ID>` with an AWS VPC ID to be able to deploy. 

At this point you can now synthesize the CloudFormation template for this code.

```
$ make synth
```

Now you can deploy the CloudFormation to AWS.

```
$ make deploy
```

You can now begin exploring the source code, contained in the directory.
There are basic unit tests included that can be run like this:

```
$ make test
```

To add additional dependencies, for example other CDK libraries, you will need to run a `poetry` command.

```
$ poetry add <package_name>
```

## Useful commands
If you wish to run these ny of the following commands for this project 
you will need to prefix them with `poetry run <command>`.
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
