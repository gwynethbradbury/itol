import app as online_learning




online_learning.onlinelearningdb.create_all()

d=[]
# GIS Machine Learning Python Flask Linux Image Processing
d.append(online_learning.models.Topic('GIS'))
d.append(online_learning.models.Topic('Machine Learning'))
d.append(online_learning.models.Topic('Python'))
d.append(online_learning.models.Topic('Flask'))
d.append(online_learning.models.Topic('Linux'))
d.append(online_learning.models.Topic('Image Processing'))


d.append(online_learning.models.Tag())
for i in d:
    online_learning.onlinelearningdb.session.add(i)
online_learning.onlinelearningdb.session.commit()

p=online_learning.models.Entry()
p.save()
c=online_learning.models.Comment(page_inst=p)
online_learning.onlinelearningdb.session.add(c)
online_learning.onlinelearningdb.session.commit()
p.tags=online_learning.models.Tag.query.all()
p.topics=online_learning.models.Topic.query.all()
p = online_learning.models.Entry.query.first()

d=[]
d.append(online_learning.models.Comment(page_inst=p))
d.append(online_learning.models.Video(page_inst=p))
for i in d:
    online_learning.onlinelearningdb.session.add(i)
online_learning.onlinelearningdb.session.commit()