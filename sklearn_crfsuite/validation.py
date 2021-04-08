from acts import *

X_train, Y_train, X_test, Y_test = get_data_sets()

print(len(X_train))
print(len(Y_train))

print(len(X_test))
print(len(Y_test))

print("nombre d'étiquettes chanson test", sum([y.count("chanson") for y in Y_test]))
print("nombre d'étiquettes chanson entrainement", sum([y.count("chanson") for y in Y_train]))

X_tv = X_train

Y_tv = Y_train

#valid_part = random.randrange(len(X_train))

best_seuil = 0.0
best_c1 = 0.0
best_c2 = 0.0
best_f = None
best_l_f1 = 0.0

best_valid_error = 1.0

for seuil in [0.1, 0.2]:
  for c1 in [0.0, 0.25]:
    for c2 in [0.0, 0.25]:
      for feature_func in [features_syl, features_default]:
        start = time.time()
        valid_error_total = 0.0
        l_f1_total = 0.0
        print("c1", c1)
        print("seuil", seuil)
        print("c2", c2)
        print("feature_func", feature_func)
        folds = 5
        for i in range(folds):
        
          print("valid fold:", i)
        
          act_heads = [find_act_heads(Y) for Y in Y_tv]
          scene_heads = [find_scene_heads(Y) for Y in Y_tv]
        
          X_train, Y_train, X_valid, Y_valid = split_test_train(
                                             [choose_rand_head(a, s, l) for a, s, l in zip(
                                              act_heads, scene_heads, [len(y) for y in Y_tv])],
                                             zip(act_heads, scene_heads), zip(X_tv, Y_tv))
          
          # TODO: meilleure vérification
          for x in X_valid:
            assert(x not in X_train)

        
          X_train = [[feature_func(x, i, seuil) for i in range(len(x))] for x in X_train]
          X_valid = [[feature_func(x, i, seuil) for i in range(len(x))] for x in X_valid] 

      
          X_train = [pycrfsuite.ItemSequence(x) for x in X_train]
          X_valid = [pycrfsuite.ItemSequence(x) for x in X_valid]
          
          crf = sklearn_crfsuite.CRF(
              algorithm='lbfgs',
              max_iterations=1000,
              all_possible_transitions=True,
              c1=c1,
              c2=c2,
          )
          
          crf.fit(X_train, Y_train)
          
          #print('best params:', rs.best_params_)
          #print('best CV score:', rs.best_score_)
          #print('model size: {:0.2f}M'.format(rs.best_estimator_.size_ / 1000000))
          
          labels = list(crf.classes_)
          
          y_valid_pred = crf.predict(X_valid)
          
          #print("F1 valid:", metrics.flat_f1_score(Y_valid, y_valid_pred,
          #                      average='weighted'))
        
          print(metrics.flat_classification_report(
            Y_valid, y_valid_pred, digits=3
          ))
          
          mistakes = 0
          for i in range(len(Y_valid)):
            for y, y_pred, x in zip(Y_valid[i], y_valid_pred[i], X_valid[i].items()):
              if y != y_pred:
                #print(y, y_pred)
                mistakes += 1
                #if y == "chanson" or y_pred == "chanson":
                #  print(x, y, y_pred)
          
          valid_error = mistakes/sum([len(Y) for Y in Y_valid])
          valid_error_total += valid_error

          l_f1 = metrics.flat_f1_score(Y_valid, y_valid_pred, labels=["chanson"], average="weighted")
          l_f1_total += l_f1

          print("l f1:", l_f1)


          print("% d'erreurs validation:", 100*mistakes/sum([len(Y) for Y in Y_valid]))

          char_f = open("bastian_char_list.txt")

          characters = char_f.read().split("\n")
      
          X_tv_ = [[feature_func(x, i, 0.1) for i in range(len(x))] for x in X_tv]
          X_tv_ = [pycrfsuite.ItemSequence(x) for x in X_tv_]
          #tei_generator = TEIGen([x.string for x in X_tv[3]], crf.predict(X_tv_)[3], characters)
          #print(etree.tostring(tei_generator.generate_TEI_body()))
          #print(etree.tostring(generate_TEI_body([x.string for x in X_tv[0]], crf.predict(X_tv_)[0]), pretty_print=True))
          
          #y_train_pred = crf.predict(X_train)
          #print("F1 train:", metrics.flat_f1_score(Y_train, y_train_pred,
          #                    average='weighted'))
        print("average l f1", l_f1_total/folds)
        print("avg_valid_error", valid_error_total/folds)
        if l_f1_total/folds > best_l_f1:
          best_valid_error = valid_error_total/folds
          best_seuil = seuil
          best_c1 = c1
          best_c2 = c2
          best_f = feature_func
          best_l_f1 = l_f1_total/folds
        print("Time elapsed for", folds, "folds:", time.time() - start)

print("best seuil:", best_seuil)
print("best c1:", best_c1)
print("best c2:", best_c2)
print("best f:", best_f)
print("best valid error:", best_valid_error)
print("best l f1:", best_l_f1)
