function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getPage(page) {
  // returns the uid of a specific page in your graph.
  // _page_: the title of the page.
  let results = window.roamAlphaAPI.q(`
    [:find ?uid
     :in $ ?title
     :where
     [?page :node/title ?title]
     [?page :block/uid ?uid]
    ]`, page);
  if (results.length) {
    return results[0][0];
  }
}

async function getOrCreatePage(page) {
  // returns the uid of a specific page in your graph, creating it first if it does not already exist.
  // _page_: the title of the page.
  roamAlphaAPI.createPage({page: {title: page}});
  let result;
  while (!result) {
    await sleep(25);
    result = getPage(page);
  }
  return result;
}

function getBlockOnPage(page, block) {
  // returns the uid of a specific block on a specific page.
  // _page_: the title of the page.
  // _block_: the text of the block.
  let results = window.roamAlphaAPI.q(`
    [:find ?block_uid
     :in $ ?page_title ?block_string
     :where
     [?page :node/title ?page_title]
     [?page :block/uid ?page_uid]
     [?block :block/parents ?page]
     [?block :block/string ?block_string]
     [?block :block/uid ?block_uid]
    ]`, page, block);
  if (results.length) {
    return results[0][0];
  }
}

async function createBlockOnPage(page, block, order) {
  // creates a new top-level block on a specific page, returning the new block's uid.
  // _page_: the title of the page.
  // _block_: the text of the block.
  // _order_: (optional) controls where to create the block, 0 for top of page, -1 for bottom of page.
  let page_uid = getPage(page);
  return createChildBlock(page_uid, block, order);
}

async function getOrCreateBlockOnPage(page, block, order) {
  // returns the uid of a specific block on a specific page, creating it first as a top-level block if it's not already there.
  // _page_: the title of the page.
  // _block_: the text of the block.
  // _order_: (optional) controls where to create the block, 0 for top of page, -1 for bottom of page.
  let block_uid = getBlockOnPage(page, block);
  if (block_uid) return block_uid;
  return createBlockOnPage(page, block, order);
}

function getChildBlock(parent_uid, block) {
  // returns the uid of a specific child block underneath a specific parent block.
  // _parent_uid_: the uid of the parent block.
  // _block_: the text of the child block.
  let results = window.roamAlphaAPI.q(`
    [:find ?block_uid
     :in $ ?parent_uid ?block_string
     :where
     [?parent :block/uid ?parent_uid]
     [?block :block/parents ?parent]
     [?block :block/string ?block_string]
     [?block :block/uid ?block_uid]
    ]`, parent_uid, block);
  if (results.length) {
    return results[0][0];
  }
}

async function getOrCreateChildBlock(parent_uid, block, order) {
  // creates a new child block underneath a specific parent block, returning the new block's uid.
  // _parent_uid_: the uid of the parent block.
  // _block_: the text of the new block.
  // _order_: (optional) controls where to create the block, 0 for inserting at the top, -1 for inserting at the bottom.
  let block_uid = getChildBlock(parent_uid, block);
  if (block_uid) return block_uid;
  return createChildBlock(parent_uid, block, order);
}

async function createChildBlock(parent_uid, block, order) {
  // returns the uid of a specific child block underneath a specific parent block, creating it first if it's not already there.
  // _parent_uid_: the uid of the parent block.
  // _block_: the text of the child block.
  // _order_: (optional) controls where to create the block, 0 for inserting at the top, -1 for inserting at the bottom.
  if (!order) {
    order = 0;
  }
  window.roamAlphaAPI.createBlock(
    {
      "location": {"parent-uid": parent_uid, "order": order},
      "block": {"string": block}
    }
  );
  let block_uid;
  while (!block_uid) {
    await sleep(25);
    block_uid = getChildBlock(parent_uid, block);
  }
  return block_uid;
}

window.sleep = sleep;
window.getPage = getPage;
window.getOrCreatePage = getOrCreatePage;
window.getBlockOnPage = getBlockOnPage;
window.createBlockOnPage = createBlockOnPage;
window.getOrCreateBlockOnPage = getOrCreateBlockOnPage;
window.getChildBlock = getChildBlock;
window.getOrCreateChildBlock = getOrCreateChildBlock;
window.createChildBlock = createChildBlock;
// END COPIED FROM https://davidbieber.com/snippets/2021-02-12-javascript-functions-for-inserting-blocks-in-roam/

let nthDate = d => {
  if (d > 3 && d < 21) return 'th';
  switch (d % 10) {
    case 1:
      return 'st';
    case 2:
      return 'nd';
    case 3:
      return 'rd';
    default:
      return 'th';
  }
}
window.nthDate = nthDate;

let getRoamDate = dateString => {
  let monthsDateProcessing = [
      'January', 'February', 'March', 'April', 'May',' June',
      'July', 'August', 'September', 'October', 'November', 'December'];

  const d = new Date(dateString);
  const year = d.getFullYear();
  const date = d.getDate();
  const month = monthsDateProcessing[d.getMonth()];
  const nthStr = nthDate(date);
  return `${month} ${date}${nthStr}, ${year}`;
}
window.getRoamDate = getRoamDate

async function insertGoNoteGoNote(note) {
  let $roam_date = getRoamDate(new Date());

  // Add the note to the daily notes page.
  let block_uid = await getOrCreateBlockOnPage($roam_date, '[[Go Note Go]] Notes:', -1);
  let note_block = await createChildBlock(block_uid, note, -1);
  return note_block
}
window.insertGoNoteGoNote = insertGoNoteGoNote;
