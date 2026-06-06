# bpd_helper
Helper library to make writing borderlands 2 and TPS Behaviour Provider Definitions easier

Make sure to check out the [BPD Classroom](https://github.com/BLCM/BLCMods/wiki/BPD-classroom) for the basics of how BPDs work.  
The [example](example.py) is provided as a recreation of the amp shield skill, with the [output](GD_Shields.Skills.Impact_Shield_Skill.BehaviorProviderDefinition_0[0].txt).

[output_links](output_links.py) contains enums for the different output link IDs of behaviors, this helps to make BPD scripts more readable while also not having to memorize what link ID means what. This is not an extensive collection, as I've mostly just implemented the ones I've been using, so PRs to add more are always welcome.

[variable_link_templates](variable_link_templates.py) contains classes to represent behaviors and objects with bpd events with templates for the variable inputs and outputs, to make it easier to deal with inputs and outputs as remembering exact naming is annoying. Like with output_links, this is not extensive so PRs are welcome.