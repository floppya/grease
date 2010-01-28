import unittest

class TestCollisionComp(dict):

	def __init__(self):
		self.new_entity_ids = set()
		self.deleted_entity_ids = set()

	def __iter__(self):
		return self.itervalues()
	
	def add(self, id, left, top, right, bottom, from_mask=0xffffffff, into_mask=0xffffffff):
		self[id] = Data(entity_id=id, 
			AABB=Data(left=left, top=top, right=right, bottom=bottom),
			from_mask=from_mask, into_mask=into_mask)

class TestManager(object):

	def __init__(self):
		self.components = self
		self.collision = TestCollisionComp()

	def __getitem__(self, name):
		return self.collision

class Data(object):

	def __init__(self, **kw):
		self.__dict__.update(kw)


class SAPCollisionTestCase(unittest.TestCase):

	def test_before_run(self):
		# Queries should be well behaved even before the controller is run
		from grease.controller.collision import SAPCollision
		coll = SAPCollision()
		self.assertEqual(coll.collision_pairs, set())
		self.assertEqual(coll.query_point(0,0), set())
	
	def test_collision_pairs_no_collision(self):
		from grease.controller.collision import SAPCollision
		manager = TestManager()
		coll = SAPCollision()
		add = manager.collision.add
		add(1, 10, 10, 20, 20)
		add(2, 0, 0, 3, 3)
		add(3, 11, 21, 15, 40)
		add(4, -5, 0, -3, 100)
		coll.add_manager(manager)
		self.assertTrue(coll.manager is manager)
		coll.run(0)
		self.assertEqual(coll.collision_pairs, set())
		coll.run(0)
		self.assertEqual(coll.collision_pairs, set())


if __name__ == '__main__':
	unittest.main()
