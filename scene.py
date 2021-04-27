# -*- coding: utf-8 -*-

class Scene(object):
    """ Container for Scene """

    class Bridge(object):

        def __init__(self, bridge):
            self.bridge = bridge

        # Scenes #####
        @property
        def scenes(self):
            return [Scene(k, **v) for k, v in self.get_scene().items()]

        def create_group_scene(self, name, group):
            """Create a Group Scene

            Group scenes are based on the definition of groups and contain always all
            lights from the selected group. No other lights from other rooms can be
            added to a group scene and the group scene can not contain less lights
            as available in the selected group. If a group is extended with new lights,
            the new lights are added with default color to all group scenes based on
            the corresponding group. This app has no influence on this behavior, it
            was defined by Philips.

            :param name: The name of the scene to be created
            :param group: The group id of where the scene will be added
            :return:
            """
            data = {
                "name": name,
                "group": group,
                "recycle": True,
                "type": "GroupScene"
            }
            return self.bridge.bridge.post('/scenes', data)

        def modify_scene(self, scene_id, data):
            return self.bridge.bridge.put('/scenes/' + scene_id, data)

        def get_scene(self):
            return self.bridge.bridge.get('/scenes')

        def activate_scene(self, group_id, scene_id, transition_time=4):
            return self.bridge.bridge.put('/groups/' +
                                str(group_id) + '/action',
                                {
                                    "scene": scene_id,
                                    "transitiontime": transition_time
                                })

        def run_scene(self, group_name, scene_name, transition_time=4):
            """Run a scene by group and scene name.

            As of 1.11 of the Hue API the scenes are accessable in the
            API. With the gen 2 of the official HUE app everything is
            organized by room groups.

            This provides a convenience way of activating scenes by group
            name and scene name. If we find exactly 1 group and 1 scene
            with the matching names, we run them.

            If we find more than one we run the first scene who has
            exactly the same lights defined as the group. This is far from
            perfect, but is convenient for setting lights symbolically (and
            can be improved later).

            :param transition_time: The duration of the transition from the
            light’s current state to the new state in a multiple of 100ms
            :returns True if a scene was run, False otherwise

            """
            groups = [x for x in self.groups if x.name == group_name]
            scenes = [x for x in self.scenes if x.name == scene_name]
            if len(groups) != 1:
                logger.warn("run_scene: More than 1 group found by name {}".format(group_name))
                return False
            group = groups[0]
            if len(scenes) == 0:
                logger.warn("run_scene: No scene found {}".format(scene_name))
                return False
            if len(scenes) == 1:
                self.activate_scene(group.group_id, scenes[0].scene_id, transition_time)
                return True
            # otherwise, lets figure out if one of the named scenes uses
            # all the lights of the group
            group_lights = sorted([x.light_id for x in group.lights])
            for scene in scenes:
                if group_lights == scene.lights:
                    self.activate_scene(group.group_id, scene.scene_id, transition_time)
                    return True
            logger.warn("run_scene: did not find a scene: {} "
                        "that shared lights with group {}".format(scene_name, group_name))
            return False

        def delete_scene(self, scene_id):
            try:
                return self.bridge.delete('/scenes/' + str(scene_id))
            except:
                logger.debug("Unable to delete scene with ID {0}".format(scene_id))

    def __init__(self, sid, appdata=None, lastupdated=None,
                 lights=None, locked=False, name="", owner="",
                 picture="", recycle=False, version=0, type="", group="",
                 *args, **kwargs):
        self.scene_id = sid
        self.appdata = appdata or {}
        self.lastupdated = lastupdated
        if lights is not None:
            self.lights = sorted([int(x) for x in lights])
        else:
            self.lights = []
        self.locked = locked
        self.name = name
        self.owner = owner
        self.picture = picture
        self.recycle = recycle
        self.version = version
        self.type = type
        self.group = group

    def __repr__(self):
        # like default python repr function, but add scene name
        return '<{0}.{1} id="{2}" name="{3}" lights={4}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.scene_id,
            self.name,
            self.lights)
